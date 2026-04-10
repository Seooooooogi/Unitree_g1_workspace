# g1_workspace — Project Memory

## Project
- **Goal**: Xbox 컨트롤러로 G1 humanoid robot 보행 제어 (MuJoCo 시뮬레이터)
- **Next**: 티칭 데이터 수집 및 강화학습 배포 가능성 검토
- **Timeline**: ~2주, solo
- **Real robot**: 미보유 — 시뮬레이터 전용

## Stack
- Python + C++ (각각 독립 Python/C++ 시뮬레이터 병행)
- MuJoCo 3.3.6 + Unitree SDK2 + CycloneDDS 0.10.2
- Xbox 컨트롤러 입력: pygame joystick
- **패키지 관리: uv 사용** → `pip install` 대신 `uv pip install` 사용

## Key Paths
- C++ 시뮬레이터: `unitree_mujoco/simulate/`
- Python 시뮬레이터: `unitree_mujoco/simulate_python/`
- 제어 스크립트: `scripts/`
- G1 MJCF 모델: `unitree_mujoco/unitree_robots/g1/`
- G1 모터 인덱스: `unitree_mujoco/unitree_robots/g1/g1_joint_index_dds.md`

## DDS Convention
- `domain_id=1`, `interface=lo` → simulation
- `domain_id=0`, `interface=enp*` → real robot (미보유)
- G1 IDL: `unitree_hg` (35 indices, 29 active DOF)

## Roadmap Status
- Phase 1: 대부분 완료 (1-4, 1-5 진행 중)
- Phase 2-1: 완료 (Xbox 컨트롤러 입력 매핑 설계)
- Phase 2-2: 다음 (G1 보행 제어 명령 구현)

## Decisions
- ai-constitution.md Rule 4 (doosan package immutability): g1_workspace에 해당 패키지 없음 → 무영향
- ai-constitution.md 전역 파일 현행 유지 (g1 전용 규칙은 CLAUDE.md에만)

---
_Last updated: 2026-04-09_
