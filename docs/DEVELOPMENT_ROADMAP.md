# g1_workspace — Development Roadmap

**Goal**: Xbox 컨트롤러로 G1 humanoid robot 보행 제어 (MuJoCo 시뮬레이터)
**Timeline**: ~2주 (solo)
**Next milestone**: 컨트롤러 입력 → G1 보행 동작 시뮬레이터 검증

---

## Phase 1: Foundation (현재)
- [x] 1-1. MuJoCo + Unitree SDK2 시뮬레이터 환경 구성
- [x] 1-2. DDS 통신 검증 (test_dds_topics.py, test_dds_receive.py)
- [x] 1-3. G1 arm 기본 제어 스크립트 (arm_low_basic.py)
- [x] 1-4. 루트 `.gitignore` 설정
- [x] 1-5. 기본 테스트 스위트 정비

## Phase 2: Xbox Controller → G1 Walking
- [x] 2-1. Xbox 컨트롤러 입력 매핑 설계 (스틱 → 보행 속도/방향)
- [ ] 2-2. G1 보행 제어 명령 구현 (LowCmd via DDS)
- [ ] 2-3. Python 시뮬레이터에서 컨트롤러 보행 검증
- [ ] 2-4. C++ 시뮬레이터에서 동일 검증

## Phase 3: 데이터 수집 기반 마련
- [ ] 3-1. 보행 중 LowState 데이터 로깅 구조 설계
- [ ] 3-2. 티칭 데이터 수집 스크립트 (컨트롤러 입력 + 상태 기록)
- [ ] 3-3. 수집 데이터 포맷 정의 (numpy, jsonl 등)

## Backlog (미정)
- [ ] 강화학습 환경 래퍼 (Gymnasium 등) 검토
- [ ] 학습된 정책 시뮬레이터 배포 파이프라인
- [ ] 실물 G1 로봇 배포 준비 (실물 확보 시)
