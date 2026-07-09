# Test Plan

1. git pull
2. bash scripts/setup_pi.sh
3. cp .env.example .env
4. edit .env
5. python -m pi_assistant.main smoke-test
6. bash scripts/list_audio_devices.sh
7. set MIC_DEVICE if needed
8. bash scripts/test_mic.sh
9. listen to test MP3
10. python -m pi_assistant.main record
11. verify local transcript
12. verify Supabase row if configured
13. python -m pi_assistant.main dashboard
14. wire button to physical pin 11 / GPIO17 and physical pin 6 / GND
15. python -m pi_assistant.main gpio-test
16. python -m pi_assistant.main gpio-record
17. python -m pi_assistant.main ui
18. press button once and verify status becomes RECORDING
19. press button again and verify status becomes PROCESSING then DONE
20. verify latest transcript, local audio path, and Supabase status appear
21. bash scripts/install_desktop_launcher.sh
22. double-click Paul Pi Assistant on the desktop
23. verify the full-screen UI opens without typing commands
