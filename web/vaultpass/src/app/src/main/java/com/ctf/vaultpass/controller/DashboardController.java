package com.ctf.vaultpass.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpSession;
import java.util.Collections;
import java.util.List;
import java.util.Map;

@Controller
public class DashboardController {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    // ----------------------------------------------------------------
    // GET /dashboard
    // ----------------------------------------------------------------
    @GetMapping("/dashboard")
    public String dashboard(HttpSession session, Model model) {
        Integer userId = (Integer) session.getAttribute("userId");

        List<Map<String, Object>> entries;
        try {
            entries = jdbcTemplate.queryForList(
                "SELECT id, site_name, site_url, vault_username, vault_password, notes, created_at " +
                "FROM vault_entries WHERE user_id = ? ORDER BY site_name ASC",
                userId
            );
        } catch (Exception e) {
            entries = Collections.emptyList();
        }

        model.addAttribute("entries", entries);
        model.addAttribute("username", session.getAttribute("username"));
        model.addAttribute("isAdmin",  session.getAttribute("isAdmin"));
        return "dashboard";
    }

    // ----------------------------------------------------------------
    // POST /vault/add
    // ----------------------------------------------------------------
    @PostMapping("/vault/add")
    public String addEntry(@RequestParam String siteName,
                           @RequestParam(required = false) String siteUrl,
                           @RequestParam(required = false) String vaultUsername,
                           @RequestParam(required = false) String vaultPassword,
                           @RequestParam(required = false) String notes,
                           HttpSession session) {
        Integer userId = (Integer) session.getAttribute("userId");
        try {
            jdbcTemplate.update(
                "INSERT INTO vault_entries (user_id, site_name, site_url, vault_username, vault_password, notes) " +
                "VALUES (?, ?, ?, ?, ?, ?)",
                userId,
                siteName,
                siteUrl      != null ? siteUrl      : "",
                vaultUsername != null ? vaultUsername : "",
                vaultPassword != null ? vaultPassword : "",
                notes        != null ? notes        : ""
            );
        } catch (Exception ignored) {}
        return "redirect:/dashboard";
    }

    // ----------------------------------------------------------------
    // POST /vault/delete/{id}
    // ----------------------------------------------------------------
    @PostMapping("/vault/delete/{id}")
    public String deleteEntry(@PathVariable int id, HttpSession session) {
        Integer userId = (Integer) session.getAttribute("userId");
        try {
            jdbcTemplate.update(
                "DELETE FROM vault_entries WHERE id = ? AND user_id = ?",
                id, userId
            );
        } catch (Exception ignored) {}
        return "redirect:/dashboard";
    }
}
