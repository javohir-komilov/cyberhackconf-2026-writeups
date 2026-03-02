package com.ctf.vaultpass.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpSession;
import java.util.List;
import java.util.Map;

@Controller
public class AuthController {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Autowired
    private BCryptPasswordEncoder passwordEncoder;

    // ----------------------------------------------------------------
    // Landing page
    // ----------------------------------------------------------------
    @GetMapping("/")
    public String index(HttpSession session) {
        if (session.getAttribute("userId") != null) {
            return "redirect:/dashboard";
        }
        return "index";
    }

    // ----------------------------------------------------------------
    // Login
    // ----------------------------------------------------------------
    @GetMapping("/login")
    public String loginForm(HttpSession session, Model model,
                            @RequestParam(required = false) String error,
                            @RequestParam(required = false) String logout) {
        if (session.getAttribute("userId") != null) {
            return "redirect:/dashboard";
        }
        if (error != null) {
            model.addAttribute("error", "Elektron pochta yoki parol noto'g'ri.");
        }
        if (logout != null) {
            model.addAttribute("info", "Tizimdan muvaffaqiyatli chiqdingiz.");
        }
        return "login";
    }

    @PostMapping("/login")
    public String login(@RequestParam String email,
                        @RequestParam String password,
                        HttpSession session,
                        Model model) {
        try {
            // Safe parameterized query
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                "SELECT id, username, email, password_hash, is_admin FROM users WHERE email = ?",
                email
            );

            if (!rows.isEmpty()) {
                Map<String, Object> user = rows.get(0);
                String storedHash = (String) user.get("password_hash");

                if (passwordEncoder.matches(password, storedHash)) {
                    session.setAttribute("userId",   ((Number) user.get("id")).intValue());
                    session.setAttribute("username", user.get("username"));
                    session.setAttribute("email",    user.get("email"));
                    session.setAttribute("isAdmin",  user.get("is_admin"));
                    return "redirect:/dashboard";
                }
            }
        } catch (Exception ignored) {}

        model.addAttribute("error", "Elektron pochta yoki parol noto'g'ri.");
        return "login";
    }

    // ----------------------------------------------------------------
    // Logout
    // ----------------------------------------------------------------
    @GetMapping("/logout")
    public String logout(HttpSession session) {
        session.invalidate();
        return "redirect:/login?logout";
    }
}
