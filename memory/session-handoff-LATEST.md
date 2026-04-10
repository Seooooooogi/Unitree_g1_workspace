# Session Handoff — g1_workspace

_Updated: 2026-04-09_

## Current State
- /project-init + /harness-init 완료
- CLAUDE.md 업데이트됨 (Hard Rules, Secrets Policy, Dev Conventions 추가)
- docs/DEVELOPMENT_ROADMAP.md 신규 생성
- .gitignore 신규 생성
- memory/ 구조 초기화

## Active Task
다음 작업 순서:
1. **1-4**: 루트 `.gitignore` 설정 → 완료 (방금 생성)
2. **1-5**: 기본 테스트 스위트 정비
3. **2-2**: G1 보행 제어 명령 구현 (LowCmd via DDS)

## Uncommitted Changes
- CLAUDE.md (수정)
- docs/DEVELOPMENT_ROADMAP.md (신규)
- .gitignore (신규)
- memory/MEMORY.md (신규)
- memory/session-handoff-LATEST.md (신규)

## Context
- Xbox 컨트롤러 입력 매핑(2-1)은 이미 scripts/g1_joystick_controller.py에 구현됨
- 실물 로봇 미보유 → 모든 테스트는 시뮬레이터
- Python 시뮬레이터: domain_id=1, interface=lo
