package com.ctf.vaultpass;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.beans.factory.annotation.Value;

import javax.annotation.PostConstruct;
import java.io.File;

@SpringBootApplication
public class VaultPassApplication {

    @Value("${vaultpass.uploads.dir:/vaultpass_uploads}")
    private String uploadsDir;

    public static void main(String[] args) {
        SpringApplication.run(VaultPassApplication.class, args);
    }

    @PostConstruct
    public void init() {
        // Ensure uploads directory exists with open permissions
        // (CTF players write flag here via RCE)
        File uploads = new File(uploadsDir);
        if (!uploads.exists()) {
            uploads.mkdirs();
        }
        uploads.setWritable(true, false);
        uploads.setReadable(true, false);
        uploads.setExecutable(true, false);
    }
}
