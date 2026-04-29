// // SPDX-License-Identifier: MIT
// pragma solidity ^0.8.0;

// contract EnergyTrade {
//     enum Role {
//         N_A,
//         Buyer,
//         Seller
//     }
//     enum Phase {
//         DataSubmission,
//         Execution,
//         Trading
//     }

//     struct ParticipantData {
//         address id;
//         Role role;
//         uint256 energyAmount;
//         uint256 pricePerKWh;
//     }

//     struct ExecutionResult {
//         address submitter;
//         bytes32 resultHash;
//     }

//     uint256 public constant TOTAL_PARTICIPANTS = 50;
//     uint256 Phase1Duration = 20;
//     uint256 Phase2Duration = 20;
//     ParticipantData[TOTAL_PARTICIPANTS] public participantsList;
//     uint256 lastUpdateTime = block.timestamp;

//     bool public isHashComputedForRound;

//     mapping(address => uint256) public addressToSlot;
//     uint256 public nextAvailableSlot = 1;
//     uint256 public currentRound = 1;
//     Phase public currentPhase = Phase.DataSubmission;

//     bytes32 public previousHash;
//     bytes32 public previousHashExecution;
//     bytes32 public finalHash;

//     ExecutionResult[5] public submittedResults;
//     uint256 public resultSubmissionCount = 0;

//     mapping(address => bool) public hasSubmittedResult;
//     mapping(bytes32 => uint256) public hashCounts; // should be in memory instead of storage.

//     event DataSubmitted(
//         address indexed participant,
//         uint256 slot,
//         Role role,
//         uint256 energy,
//         uint256 price
//     );
//     event PhaseChanged(uint256 round, Phase newPhase);
//     event FinalResultHash(bytes32 resultHash, uint256 roundNumber);

//     // modifier onlyPhase(Phase requiredPhase) {
//     //     require(currentPhase == requiredPhase, "Not allowed in this phase");
//     //     _;
//     // }

//     modifier onlyPhase(Phase requiredPhase) {
//         require(
//             currentPhase == requiredPhase,
//             "Please wait for next round,Currently we are in phase 2 (Execution Result)"
//         );
//         _;
//     }

//     modifier onlyPhaseExecution(Phase requiredPhase) {
//         require(
//             currentPhase == requiredPhase,
//             "Please go for next round,Currently we are in phase 1 (Data Submission)"
//         );
//         _;
//     }

//     constructor() {
//         for (uint256 i = 0; i < TOTAL_PARTICIPANTS; i++) {
//             participantsList[i] = ParticipantData({
//                 id: address(0),
//                 role: Role.N_A,
//                 energyAmount: 0,
//                 pricePerKWh: 0
//             });
//         }
//     }

//     function register() public onlyPhase(Phase.DataSubmission) {
//         require(
//             addressToSlot[msg.sender] == 0,
//             "Participant already registered"
//         );
//         require(nextAvailableSlot <= TOTAL_PARTICIPANTS, "No available slots");
//         addressToSlot[msg.sender] = nextAvailableSlot;
//         nextAvailableSlot += 1;
//     }

//     // Phase 1
//     // function submitData(
//     //     Role _role,
//     //     uint256 _energyAmount,
//     //     uint256 _pricePerKWh
//     // ) public onlyPhase(Phase.DataSubmission) {
//     //     require(addressToSlot[msg.sender] != 0, "Participant not registered");
//     //     uint256 slot = addressToSlot[msg.sender];
//     //     require(
//     //         participantsList[slot].energyAmount == 0,
//     //         "Data already submitted in the current round"
//     //     );

//     //     participantsList[slot] = ParticipantData({
//     //         id: msg.sender,
//     //         role: _role,
//     //         energyAmount: _energyAmount,
//     //         pricePerKWh: _pricePerKWh
//     //     });

//     //     emit DataSubmitted(
//     //         msg.sender,
//     //         slot,
//     //         _role,
//     //         _energyAmount,
//     //         _pricePerKWh
//     //     );
//     // }

//     function submitData(
//         Role _role,
//         uint256 _energyAmount,
//         uint256 _pricePerKWh
//     ) public onlyPhase(Phase.DataSubmission) {
//         // if (block.timestamp - lastUpdateTime >= Phase1Duration) {
//         //     hashParticipantsList();
//         //     advancePhase();
//         //     lastUpdateTime = block.timestamp;
//         //     return;
//         // }

//         require(
//             block.timestamp - lastUpdateTime < Phase1Duration,
//             "Phase 1 window has closed, submission rejected"
//         );

//         require(addressToSlot[msg.sender] != 0, "Participant not registered");
//         uint256 slot = addressToSlot[msg.sender];
//         require(slot >= 1 && slot <= TOTAL_PARTICIPANTS, "Invalid slot"); // defensive

//         uint256 idx = slot - 1; // convert to 0-based index

//         require(
//             participantsList[idx].energyAmount == 0,
//             "Data already submitted in the current round"
//         );

//         participantsList[idx] = ParticipantData({
//             id: msg.sender,
//             role: _role,
//             energyAmount: _energyAmount,
//             pricePerKWh: _pricePerKWh
//         });

//         emit DataSubmitted(
//             msg.sender,
//             slot,
//             _role,
//             _energyAmount,
//             _pricePerKWh
//         );
//     }

//     function advancePhase() public {
//         if (currentPhase == Phase.DataSubmission) {
//             currentPhase = Phase.Execution;
//         } else if (currentPhase == Phase.Execution) {
//             currentPhase = Phase.Trading;
//         } else if (currentPhase == Phase.Trading) {
//             currentPhase = Phase.DataSubmission;
//             currentRound++;

//             for (uint256 i = 0; i < TOTAL_PARTICIPANTS; i++) {
//                 participantsList[i].role = Role.N_A;
//                 participantsList[i].energyAmount = 0;
//                 participantsList[i].pricePerKWh = 0;
//             }

//             for (uint256 i = 0; i < resultSubmissionCount; i++) {
//                 hasSubmittedResult[submittedResults[i].submitter] = false;
//                 submittedResults[i].submitter = address(0);
//                 submittedResults[i].resultHash = bytes32(0);
//             }

//             resultSubmissionCount = 0;
//             isHashComputedForRound = false;
//         }

//         emit PhaseChanged(currentRound, currentPhase);
//     }

//     function hashParticipantsList()
//         public
//         onlyPhase(Phase.DataSubmission)
//         returns (bytes32)
//     {
//         if (block.timestamp - lastUpdateTime >= Phase1Duration) {
//             advancePhase();
//             lastUpdateTime = block.timestamp;
//             return 0;
//         }
//         require(
//             !isHashComputedForRound,
//             "Hash already computed for this round"
//         );

//         bytes memory encodedData;
//         for (uint256 i = 0; i < TOTAL_PARTICIPANTS; i++) {
//             ParticipantData memory participant = participantsList[i];
//             encodedData = abi.encodePacked(
//                 encodedData,
//                 participant.id,
//                 participant.role,
//                 participant.energyAmount,
//                 participant.pricePerKWh
//             );
//         }

//         bytes32 currentHash = keccak256(encodedData);
//         if (previousHash == bytes32(0)) {
//             previousHash = keccak256(
//                 abi.encodePacked(currentHash, currentHash)
//             );
//         } else {
//             previousHash = keccak256(
//                 abi.encodePacked(previousHash, currentHash)
//             );
//         }

//         isHashComputedForRound = true;

//         return previousHash;
//     }

//     // Phase 2
//     // function submitExecutionResult(
//     //     bytes32 resultHash
//     // ) public onlyPhase(Phase.Execution) {
//     //     require(
//     //         resultSubmissionCount <= 5,
//     //         "Maximum 5 results already submitted."
//     //     );
//     //     require(
//     //         !hasSubmittedResult[msg.sender],
//     //         "You have already submitted a result."
//     //     );

//     //     submittedResults[resultSubmissionCount] = ExecutionResult({
//     //         submitter: msg.sender,
//     //         resultHash: resultHash
//     //     });

//     //     hasSubmittedResult[msg.sender] = true;
//     //     resultSubmissionCount++;
//     // }
//     function submitExecutionResult(
//         bytes32 resultHash
//     ) public onlyPhaseExecution(Phase.Execution) {
//         // ensure there is space

//         // if (
//         //     (currentPhase == Phase.DataSubmission) &&
//         //     (block.timestamp - lastUpdateTime >= Phase1Duration)
//         // ) {
//         //     hashParticipantsList();
//         //     advancePhase();
//         //     lastUpdateTime = block.timestamp;
//         // } else if (
//         //     (currentPhase == Phase.Execution) &&
//         //     (block.timestamp - lastUpdateTime >= Phase2Duration)
//         // ) {
//         //     advancePhase();
//         //     lastUpdateTime = block.timestamp;
//         //     return;
//         // }
//         if (
//             (currentPhase == Phase.Execution) &&
//             (block.timestamp - lastUpdateTime >= Phase2Duration)
//         ) {
//             advancePhase();
//             lastUpdateTime = block.timestamp;
//             return;
//         }

//         require(
//             resultSubmissionCount < submittedResults.length,
//             "Maximum 5 results already submitted."
//         );
//         require(
//             !hasSubmittedResult[msg.sender],
//             "You have already submitted a result."
//         );

//         submittedResults[resultSubmissionCount] = ExecutionResult({
//             submitter: msg.sender,
//             resultHash: resultHash
//         });

//         hasSubmittedResult[msg.sender] = true;
//         resultSubmissionCount++;
//     }

//     function verifyExecutionResult()
//         public
//         onlyPhaseExecution(Phase.Execution)
//         returns (bytes32 majorityHash, bool isVerified)
//     {
//         // if (
//         //     (currentPhase == Phase.DataSubmission) &&
//         //     (block.timestamp - lastUpdateTime >= Phase1Duration)
//         // ) {
//         //     hashParticipantsList();
//         //     advancePhase();
//         //     lastUpdateTime = block.timestamp;
//         // } else if (
//         //     (currentPhase == Phase.Execution) &&
//         //     (block.timestamp - lastUpdateTime >= Phase2Duration)
//         // ) {
//         //     advancePhase();
//         //     lastUpdateTime = block.timestamp;
//         //     return (0, false);
//         // }

//         if (
//             (currentPhase == Phase.Execution) &&
//             (block.timestamp - lastUpdateTime >= Phase2Duration)
//         ) {
//             advancePhase();
//             lastUpdateTime = block.timestamp;
//             return (bytes32(0), false);
//         }

//         uint256 validSubmissions = 0;

//         for (uint256 i = 0; i < submittedResults.length; i++) {
//             bytes32 h = submittedResults[i].resultHash;
//             if (h != bytes32(0)) {
//                 hashCounts[h]++;
//                 validSubmissions++;
//             }
//         }

//         if (validSubmissions == 0) {
//             return (bytes32(0), false);
//         }

//         for (uint256 i = 0; i < submittedResults.length; i++) {
//             bytes32 h = submittedResults[i].resultHash;
//             if (h != bytes32(0) && hashCounts[h] > validSubmissions / 2) {
//                 if (previousHashExecution == bytes32(0)) {
//                     previousHashExecution = keccak256(abi.encodePacked(h, h));
//                 } else {
//                     previousHashExecution = keccak256(
//                         abi.encodePacked(previousHashExecution, h)
//                     );
//                 }
//                 finalHash = h;
//                 emit FinalResultHash(finalHash, currentRound);
//                 advancePhase();
//                 lastUpdateTime = block.timestamp;
//                 return (h, true);
//             }
//         }

//         finalHash = bytes32(0);
//         emit FinalResultHash(finalHash, currentRound);
//         advancePhase();
//         lastUpdateTime = block.timestamp;
//         return (bytes32(0), false);
//     }
// }

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EnergyTrade {
    enum Role {
        N_A,
        Buyer,
        Seller
    }
    enum Phase {
        DataSubmission,
        Execution
    }

    struct ParticipantData {
        address id;
        Role role;
        uint256 energyAmount;
        uint256 pricePerKWh;
    }

    struct ExecutionResult {
        address submitter;
        bytes32 resultHash;
    }

    uint256 public constant TOTAL_PARTICIPANTS = 10;
    uint256 public constant PHASE_DURATION = 20 minutes;

    ParticipantData[TOTAL_PARTICIPANTS] public participantsList;
    bool public isHashComputedForRound;

    mapping(address => uint256) public addressToSlot;
    uint256 public nextAvailableSlot = 1;
    uint256 public currentRound = 1;

    Phase public currentPhase = Phase.DataSubmission;
    uint256 public phaseStartTime;

    bytes32 public previousHash;
    bytes32 public previousHashExecution;
    bytes32 public finalHash;

    ExecutionResult[5] public submittedResults;
    uint256 public resultSubmissionCount = 0;

    mapping(address => bool) public hasSubmittedResult;
    mapping(bytes32 => uint256) public hashCounts;

    event DataSubmitted(
        address indexed participant,
        uint256 slot,
        Role role,
        uint256 energy,
        uint256 price
    );
    event PhaseChanged(uint256 round, Phase newPhase);
    event RoundCompleted(uint256 completedRound);

    // ─── Auto-advance modifier ────────────────────────────────────────────────
    modifier checkAndAdvancePhase() {
        if (block.timestamp >= phaseStartTime + PHASE_DURATION) {
            _advancePhase();
        }
        _;
    }

    modifier onlyPhase(Phase requiredPhase) {
        require(currentPhase == requiredPhase, "Not allowed in this phase");
        _;
    }

    constructor() {
        phaseStartTime = block.timestamp;
        for (uint256 i = 0; i < TOTAL_PARTICIPANTS; i++) {
            participantsList[i] = ParticipantData(address(0), Role.N_A, 0, 0);
        }
    }

    // ─── Core phase transition logic ──────────────────────────────────────────
    function _advancePhase() internal {
        if (currentPhase == Phase.DataSubmission) {
            // DataSubmission → Execution (same round)
            currentPhase = Phase.Execution;
            phaseStartTime = block.timestamp;
            emit PhaseChanged(currentRound, currentPhase);
        } else if (currentPhase == Phase.Execution) {
            // Execution done → round complete → next round starts
            emit RoundCompleted(currentRound);
            currentRound++;
            currentPhase = Phase.DataSubmission;
            phaseStartTime = block.timestamp;
            _resetRound();
            emit PhaseChanged(currentRound, currentPhase);
        }
    }

    function _resetRound() internal {
        for (uint256 i = 0; i < TOTAL_PARTICIPANTS; i++) {
            participantsList[i].role = Role.N_A;
            participantsList[i].energyAmount = 0;
            participantsList[i].pricePerKWh = 0;
        }
        for (uint256 i = 0; i < resultSubmissionCount; i++) {
            hasSubmittedResult[submittedResults[i].submitter] = false;
            submittedResults[i] = ExecutionResult(address(0), bytes32(0));
        }
        resultSubmissionCount = 0;
        isHashComputedForRound = false;
    }

    // ─── Public helpers ───────────────────────────────────────────────────────

    function timeRemaining() public view returns (uint256) {
        uint256 elapsed = block.timestamp - phaseStartTime;
        if (elapsed >= PHASE_DURATION) return 0;
        return PHASE_DURATION - elapsed;
    }

    // Explicit trigger for keeper bots / when no user tx has come in
    function advancePhase() public checkAndAdvancePhase {}

    // ─── Phase 1: DataSubmission ──────────────────────────────────────────────

    function register()
        public
        checkAndAdvancePhase
        onlyPhase(Phase.DataSubmission)
    {
        require(addressToSlot[msg.sender] == 0, "Already registered");
        require(nextAvailableSlot < TOTAL_PARTICIPANTS, "No available slots");
        addressToSlot[msg.sender] = nextAvailableSlot;
        nextAvailableSlot += 1;
    }

    function submitData(
        Role _role,
        uint256 _energyAmount,
        uint256 _pricePerKWh
    ) public checkAndAdvancePhase onlyPhase(Phase.DataSubmission) {
        require(addressToSlot[msg.sender] != 0, "Not registered");
        uint256 slot = addressToSlot[msg.sender];
        require(
            participantsList[slot].energyAmount == 0,
            "Already submitted this round"
        );

        participantsList[slot] = ParticipantData(
            msg.sender,
            _role,
            _energyAmount,
            _pricePerKWh
        );
        emit DataSubmitted(
            msg.sender,
            slot,
            _role,
            _energyAmount,
            _pricePerKWh
        );
    }

    function hashParticipantsList()
        public
        checkAndAdvancePhase
        onlyPhase(Phase.DataSubmission)
        returns (bytes32)
    {
        require(
            !isHashComputedForRound,
            "Hash already computed for this round"
        );

        bytes memory encodedData;
        for (uint256 i = 0; i < TOTAL_PARTICIPANTS; i++) {
            ParticipantData memory p = participantsList[i];
            encodedData = abi.encodePacked(
                encodedData,
                p.id,
                p.role,
                p.energyAmount,
                p.pricePerKWh
            );
        }

        bytes32 currentHash = keccak256(encodedData);
        previousHash = previousHash == bytes32(0)
            ? keccak256(abi.encodePacked(currentHash, currentHash))
            : keccak256(abi.encodePacked(previousHash, currentHash));

        isHashComputedForRound = true;
        return previousHash;
    }

    // ─── Phase 2: Execution ───────────────────────────────────────────────────

    function submitExecutionResult(
        bytes32 resultHash
    ) public checkAndAdvancePhase onlyPhase(Phase.Execution) {
        require(
            resultSubmissionCount < 5,
            "Maximum 5 results already submitted"
        );
        require(!hasSubmittedResult[msg.sender], "Already submitted");

        submittedResults[resultSubmissionCount] = ExecutionResult(
            msg.sender,
            resultHash
        );
        hasSubmittedResult[msg.sender] = true;
        resultSubmissionCount++;
    }

    function verifyExecutionResult()
        public
        checkAndAdvancePhase
        onlyPhase(Phase.Execution)
        returns (bytes32 majorityHash, bool isVerified)
    {
        uint256 validSubmissions = 0;

        for (uint256 i = 0; i < submittedResults.length; i++) {
            bytes32 h = submittedResults[i].resultHash;
            if (h != bytes32(0)) {
                hashCounts[h]++;
                validSubmissions++;
            }
        }

        if (validSubmissions == 0) return (bytes32(0), false);

        for (uint256 i = 0; i < submittedResults.length; i++) {
            bytes32 h = submittedResults[i].resultHash;
            if (h != bytes32(0) && hashCounts[h] > validSubmissions / 2) {
                previousHashExecution = previousHashExecution == bytes32(0)
                    ? keccak256(abi.encodePacked(h, h))
                    : keccak256(abi.encodePacked(previousHashExecution, h));
                finalHash = h;
                return (h, true);
            }
        }

        finalHash = bytes32(0);
        return (bytes32(0), false);
    }
}
