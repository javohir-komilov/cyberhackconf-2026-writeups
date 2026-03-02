package com.ctf.vaultpass.controller;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import javax.servlet.http.HttpSession;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.ByteArrayInputStream;
import java.io.ObjectInputStream;
import java.util.Base64;

/**
 * ImportController — handles vault backup import.
 *
 * Vault backups are AES-128/CBC encrypted Java serialized objects.
 * The decryption key and IV are loaded from /web.ini at runtime.
 * Submitted data is base64-encoded ciphertext.
 */
@Controller
public class ImportController {

    private static final String CONFIG_FILE = "/web.ini";

    // ----------------------------------------------------------------
    // GET /import
    // ----------------------------------------------------------------
    @GetMapping("/import")
    public String importPage(HttpSession session, Model model) {
        model.addAttribute("username", session.getAttribute("username"));
        model.addAttribute("isAdmin",  session.getAttribute("isAdmin"));
        return "import";
    }

    // ----------------------------------------------------------------
    // POST /import/passwords  — VULNERABLE: Java deserialization RCE
    // ----------------------------------------------------------------
    @PostMapping("/import/passwords")
    public String importPasswords(@RequestParam String importData,
                                  HttpSession session,
                                  Model model) {
        model.addAttribute("username", session.getAttribute("username"));
        model.addAttribute("isAdmin",  session.getAttribute("isAdmin"));

        try {
            // Read AES key and IV from /web.ini (not the database)
            String aesKey = readIniValue(CONFIG_FILE, "key");
            String aesIv  = readIniValue(CONFIG_FILE, "iv");

            if (aesKey == null || aesIv == null) {
                model.addAttribute("error", "Import xizmati noto'g'ri sozlangan. Administratorga murojaat qiling.");
                return "import";
            }

            byte[] encryptedBytes = Base64.getDecoder().decode(importData.trim().replace(' ', '+'));

            Cipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");
            SecretKeySpec keySpec = new SecretKeySpec(aesKey.getBytes("UTF-8"), "AES");
            IvParameterSpec  ivSpec  = new IvParameterSpec(aesIv.getBytes("UTF-8"));
            cipher.init(Cipher.DECRYPT_MODE, keySpec, ivSpec);
            byte[] decrypted = cipher.doFinal(encryptedBytes);

            // !!!! VULNERABLE: no type filter on deserialization !!!!
            // commons-collections 3.1 on classpath → ysoserial gadget chains
            ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(decrypted));
            Object imported = ois.readObject();
            ois.close();

            model.addAttribute("success",
                "Seyf zaxirasi muvaffaqiyatli import qilindi! " + countEntries(imported) + " ta parol tiklandi.");

        } catch (java.io.StreamCorruptedException | javax.crypto.BadPaddingException e) {
            model.addAttribute("error",
                "Deshifrlash muvaffaqiyatsiz: noto'g'ri ma'lumot formati yoki noto'g'ri shifrlash kaliti.");
        } catch (Exception e) {
            model.addAttribute("error", "Import xatosi: " + e.getMessage());
        }

        return "import";
    }

    /**
     * Reads a key=value pair from a simple INI-style file.
     * Ignores lines starting with '[' (section headers) and '#' (comments).
     * Values are base64-encoded; decoded bytes are returned as a UTF-8 string.
     */
    private String readIniValue(String filePath, String keyName) throws Exception {
        try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.startsWith("#") || line.startsWith("[") || line.isEmpty()) continue;
                int eq = line.indexOf('=');
                if (eq > 0 && line.substring(0, eq).trim().equals(keyName)) {
                    String b64 = line.substring(eq + 1).trim();
                    return new String(Base64.getDecoder().decode(b64), "UTF-8");
                }
            }
        }
        return null;
    }

    private String countEntries(Object obj) {
        if (obj instanceof java.util.Collection) {
            return String.valueOf(((java.util.Collection<?>) obj).size());
        }
        return "0";
    }
}
