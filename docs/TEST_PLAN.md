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
