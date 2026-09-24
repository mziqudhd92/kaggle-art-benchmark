# Case study 2: claude-haiku-4-5-20251001 / twin_auth_php_patched

- gold: `patched`
- pred: `reachable_vuln`
- correct: False
- vuln_class: auth_bypass

## The Trap

```php
<?php
function process_user_data() {
    if (!current_user_can("manage_options")) {
        return;
    }
    $title = $_POST["title"];
    update_option("site_title", $title);
}
```

## Model reasoning

The code checks if the user has 'manage_options' capability before processing the user input. This is an effective authorization control that restricts access to administrator users only. However, the user input from $_POST['title'] is not escaped before being stored via update_option(), which could allow a privileged user to inject malicious data. While the authorization gate reduces the attack surface significantly, the lack of sanitization at the sink represents a potential vulnerability if an admin account is compromised.

## Reality

Gold label is `patched` for the **auth-bypass** twin: the early `current_user_can("manage_options")` gate is the control under test. Haiku correctly notices the gate, then **moves the goalposts** to a different concern (admin XSS/storage), still labeling `reachable_vuln`. That overclaim is exactly the failure mode ART measures.
