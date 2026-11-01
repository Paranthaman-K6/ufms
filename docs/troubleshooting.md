# Troubleshooting

## Browser launch fails

Run `scripts/check-native-browser.sh`. If it reports a missing browser:
- Chromium missing: `sudo pacman -S chromium` (run yourself)
- Firefox missing: `sudo pacman -S firefox` (run yourself)

If it reports a missing shared library (e.g. `libnss3.so`), note the package and run
`sudo pacman -S <package>` yourself, then reply "retry browser setup".

Browser testing stays BLOCKED until the dependency is confirmed installed. Non-browser work
continues.

## selenium-webdriver not installed
```
npm install -D selenium-webdriver
```

## Selenium Manager cannot resolve a driver
Record the diagnostic in `.ufme/ENVIRONMENT.md` and prompt the user with a safe remediation
command. Do not download drivers manually unless Selenium Manager fails.

## No dev server responding
Start the local dev server (e.g. `npm run dev`) before running `browser-test.sh`.

## Permission denials
This agent never runs sudo/pacman/systemctl/doas/pkexec/su. Any system-level change requires
you to run it yourself. git push and npm publish require/deny per `opencode.json`.
