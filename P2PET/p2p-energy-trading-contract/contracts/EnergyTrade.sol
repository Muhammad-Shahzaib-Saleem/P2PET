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
//         EnergyTransfer
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

//     uint256 public constant TOTAL_PARTICIPANTS = 10;
//     uint256 public constant DATA_SUBMISSION_DURATION = 5 minutes;
//     uint256 public constant EXECUTION_DURATION = 5 minutes;
//     uint256 public constant ENERGY_TRANSFER_DURATION = 50 minutes;
//     uint256 public constant ROUND_DURATION = 60 minutes;

//     ParticipantData[TOTAL_PARTICIPANTS] public participantsList;
//     bool public isHashComputedForRound;

//     mapping(address => uint256) public addressToSlot;
//     uint256 public nextAvailableSlot = 1;
//     uint256 public currentRound = 1;

//     Phase public currentPhase = Phase.DataSubmission;
//     uint256 public phaseStartTime;

//     bytes32 public previousHash;
//     bytes32 public previousHashExecution;
//     bytes32 public finalHash;

//     ExecutionResult[5] public submittedResults;
//     uint256 public resultSubmissionCount = 0;

//     mapping(address => bool) public hasSubmittedResult;
//     mapping(bytes32 => uint256) public hashCounts;

//     event DataSubmitted(
//         address indexed participant,
//         uint256 slot,
//         Role role,
//         uint256 energy,
//         uint256 price
//     );
//     event PhaseChanged(uint256 round, Phase newPhase);
//     event RoundCompleted(uint256 completedRound);

//     // ─── Auto-advance modifier ────────────────────────────────────────────────
//     modifier checkAndAdvancePhase() {
//         if (block.timestamp >= phaseStartTime + _currentPhaseDuration()) {
//             _advancePhase();
//         }
//         _;
//     }

//     modifier onlyPhase(Phase requiredPhase) {
//         require(currentPhase == requiredPhase, "Not allowed in this phase");
//         _;
//     }

//     constructor() {
//         phaseStartTime = block.timestamp;
//         for (uint256 i = 0; i < TOTAL_PARTICIPANTS; i++) {
//             participantsList[i] = ParticipantData(address(0), Role.N_A, 0, 0);
//         }
//     }

//     // ─── Returns duration of the currently active phase ───────────────────────
//     function _currentPhaseDuration() internal view returns (uint256) {
//         if (currentPhase == Phase.DataSubmission)
//             return DATA_SUBMISSION_DURATION;
//         if (currentPhase == Phase.Execution) return EXECUTION_DURATION;
//         return ENERGY_TRANSFER_DURATION;
//     }

//     // ─── Core phase transition logic ──────────────────────────────────────────
//     function _advancePhase() internal {
//         if (currentPhase == Phase.DataSubmission) {
//             currentPhase = Phase.Execution;
//             phaseStartTime = block.timestamp;
//             emit PhaseChanged(currentRound, currentPhase);
//         } else if (currentPhase == Phase.Execution) {
//             currentPhase = Phase.EnergyTransfer;
//             phaseStartTime = block.timestamp;
//             emit PhaseChanged(currentRound, currentPhase);
//         } else {
//             // EnergyTransfer done → round complete → next round
//             emit RoundCompleted(currentRound);
//             currentRound++;
//             currentPhase = Phase.DataSubmission;
//             phaseStartTime = block.timestamp;
//             _resetRound();
//             emit PhaseChanged(currentRound, currentPhase);
//         }
//     }

//     function _resetRound() internal {
//         for (uint256 i = 0; i < TOTAL_PARTICIPANTS; i++) {
//             participantsList[i].role = Role.N_A;
//             participantsList[i].energyAmount = 0;
//             participantsList[i].pricePerKWh = 0;
//         }
//         for (uint256 i = 0; i < resultSubmissionCount; i++) {
//             hasSubmittedResult[submittedResults[i].submitter] = false;
//             submittedResults[i] = ExecutionResult(address(0), bytes32(0));
//         }
//         resultSubmissionCount = 0;
//         isHashComputedForRound = false;
//     }

//     // ─── Public helpers ───────────────────────────────────────────────────────

//     function timeRemaining() public view returns (uint256) {
//         uint256 duration = _currentPhaseDuration();
//         uint256 elapsed = block.timestamp - phaseStartTime;
//         if (elapsed >= duration) return 0;
//         return duration - elapsed;
//     }

//     function roundTimeRemaining() public view returns (uint256) {
//         uint256 alreadySpent;
//         if (currentPhase == Phase.Execution) {
//             alreadySpent = DATA_SUBMISSION_DURATION;
//         } else if (currentPhase == Phase.EnergyTransfer) {
//             alreadySpent = DATA_SUBMISSION_DURATION + EXECUTION_DURATION;
//         }
//         uint256 elapsed = block.timestamp - phaseStartTime;
//         uint256 totalElapsed = alreadySpent + elapsed;
//         if (totalElapsed >= ROUND_DURATION) return 0;
//         return ROUND_DURATION - totalElapsed;
//     }

//     // Explicit trigger for keeper bots
//     function advancePhase() public checkAndAdvancePhase {}

//     // ─── Phase 1: DataSubmission ──────────────────────────────────────────────

//     function register()
//         public
//         checkAndAdvancePhase
//         onlyPhase(Phase.DataSubmission)
//     {
//         require(addressToSlot[msg.sender] == 0, "Already registered");
//         require(nextAvailableSlot < TOTAL_PARTICIPANTS, "No available slots");
//         addressToSlot[msg.sender] = nextAvailableSlot;
//         nextAvailableSlot += 1;
//     }

//     function submitData(
//         Role _role,
//         uint256 _energyAmount,
//         uint256 _pricePerKWh
//     ) public checkAndAdvancePhase onlyPhase(Phase.DataSubmission) {
//         require(addressToSlot[msg.sender] != 0, "Not registered");
//         uint256 slot = addressToSlot[msg.sender];
//         require(
//             participantsList[slot].energyAmount == 0,
//             "Already submitted this round"
//         );
//         participantsList[slot] = ParticipantData(
//             msg.sender,
//             _role,
//             _energyAmount,
//             _pricePerKWh
//         );
//         emit DataSubmitted(
//             msg.sender,
//             slot,
//             _role,
//             _energyAmount,
//             _pricePerKWh
//         );
//     }

//     function hashParticipantsList()
//         public
//         checkAndAdvancePhase
//         onlyPhase(Phase.DataSubmission)
//         returns (bytes32)
//     {
//         require(
//             !isHashComputedForRound,
//             "Hash already computed for this round"
//         );

//         bytes memory encodedData;
//         for (uint256 i = 0; i < TOTAL_PARTICIPANTS; i++) {
//             ParticipantData memory p = participantsList[i];
//             encodedData = abi.encodePacked(
//                 encodedData,
//                 p.id,
//                 p.role,
//                 p.energyAmount,
//                 p.pricePerKWh
//             );
//         }

//         bytes32 currentHash = keccak256(encodedData);
//         previousHash = previousHash == bytes32(0)
//             ? keccak256(abi.encodePacked(currentHash, currentHash))
//             : keccak256(abi.encodePacked(previousHash, currentHash));

//         isHashComputedForRound = true;
//         return previousHash;
//     }

//     // ─── Phase 2: Execution ───────────────────────────────────────────────────

//     function submitExecutionResult(
//         bytes32 resultHash
//     ) public checkAndAdvancePhase onlyPhase(Phase.Execution) {
//         require(
//             resultSubmissionCount < 5,
//             "Maximum 5 results already submitted"
//         );
//         require(!hasSubmittedResult[msg.sender], "Already submitted");

//         submittedResults[resultSubmissionCount] = ExecutionResult(
//             msg.sender,
//             resultHash
//         );
//         hasSubmittedResult[msg.sender] = true;
//         resultSubmissionCount++;
//     }

//     function verifyExecutionResult()
//         public
//         checkAndAdvancePhase
//         onlyPhase(Phase.Execution)
//         returns (bytes32 majorityHash, bool isVerified)
//     {
//         uint256 validSubmissions = 0;

//         for (uint256 i = 0; i < submittedResults.length; i++) {
//             bytes32 h = submittedResults[i].resultHash;
//             if (h != bytes32(0)) {
//                 hashCounts[h]++;
//                 validSubmissions++;
//             }
//         }

//         if (validSubmissions == 0) return (bytes32(0), false);

//         for (uint256 i = 0; i < submittedResults.length; i++) {
//             bytes32 h = submittedResults[i].resultHash;
//             if (h != bytes32(0) && hashCounts[h] > validSubmissions / 2) {
//                 previousHashExecution = previousHashExecution == bytes32(0)
//                     ? keccak256(abi.encodePacked(h, h))
//                     : keccak256(abi.encodePacked(previousHashExecution, h));
//                 finalHash = h;
//                 return (h, true);
//             }
//         }

//         finalHash = bytes32(0);
//         return (bytes32(0), false);
//     }

//     // ─── Phase 3: EnergyTransfer (time-lock only, no on-chain logic) ──────────
//     // Off-chain transfers happen freely during this 50-minute window.
//     // The keeper bot advances to the next round once this phase expires.
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
        Execution,
        EnergyTransfer
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
    uint256 public constant DATA_SUBMISSION_DURATION = 10 minutes;
    uint256 public constant EXECUTION_DURATION = 10 minutes;
    uint256 public constant ENERGY_TRANSFER_DURATION = 40 minutes;
    uint256 public constant ROUND_DURATION = 60 minutes;
    uint256 public constant TRANSFER_WINDOW = 60 minutes; // 50m own phase + 10m into next round

    // round => timestamp when that round's EnergyTransfer phase opened
    mapping(uint256 => uint256) public roundTransferStart;

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
    event TransferWindowOpened(
        uint256 indexed round,
        uint256 opensAt,
        uint256 closesAt
    );
    event TransferWindowClosed(uint256 indexed round);

    // ─── Modifiers ────────────────────────────────────────────────────────────
    modifier checkAndAdvancePhase() {
        if (block.timestamp >= phaseStartTime + _currentPhaseDuration()) {
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

    // ─── Internal helpers ─────────────────────────────────────────────────────
    function _currentPhaseDuration() internal view returns (uint256) {
        if (currentPhase == Phase.DataSubmission)
            return DATA_SUBMISSION_DURATION;
        if (currentPhase == Phase.Execution) return EXECUTION_DURATION;
        return ENERGY_TRANSFER_DURATION;
    }

    function _advancePhase() internal {
        if (currentPhase == Phase.DataSubmission) {
            currentPhase = Phase.Execution;
            phaseStartTime = block.timestamp;
            emit PhaseChanged(currentRound, currentPhase);
        } else if (currentPhase == Phase.Execution) {
            // Record transfer window start for this round.
            // Window = 60 min = 50 min own phase + 10 min into next round's DataSub+Exec.
            // It closes exactly when the NEXT round's EnergyTransfer opens.
            roundTransferStart[currentRound] = block.timestamp;
            emit TransferWindowOpened(
                currentRound,
                block.timestamp,
                block.timestamp + TRANSFER_WINDOW
            );

            currentPhase = Phase.EnergyTransfer;
            phaseStartTime = block.timestamp;
            emit PhaseChanged(currentRound, currentPhase);
        } else {
            // EnergyTransfer (50 min) done → new round starts.
            // Previous round's transfer window has exactly 10 min left,
            // which covers the next round's DataSubmission(5m) + Execution(5m).
            // It closes automatically when the next round reaches EnergyTransfer.

            // Close the previous round's transfer window if somehow still tracked
            uint256 prevRound = currentRound;

            emit RoundCompleted(prevRound);
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

    // ─── Public view helpers ──────────────────────────────────────────────────

    function timeRemaining() public view returns (uint256) {
        uint256 elapsed = block.timestamp - phaseStartTime;
        uint256 duration = _currentPhaseDuration();
        if (elapsed >= duration) return 0;
        return duration - elapsed;
    }

    function roundTimeRemaining() public view returns (uint256) {
        uint256 alreadySpent;
        if (currentPhase == Phase.Execution) {
            alreadySpent = DATA_SUBMISSION_DURATION;
        } else if (currentPhase == Phase.EnergyTransfer) {
            alreadySpent = DATA_SUBMISSION_DURATION + EXECUTION_DURATION;
        }
        uint256 totalElapsed = alreadySpent +
            (block.timestamp - phaseStartTime);
        if (totalElapsed >= ROUND_DURATION) return 0;
        return ROUND_DURATION - totalElapsed;
    }

    /// @notice Seconds left in a specific round's 60-min transfer window.
    /// Window opens when that round's Execution ends.
    /// Window closes exactly when the NEXT round's EnergyTransfer opens (10 min into next round).
    function transferWindowRemaining(
        uint256 round
    ) public view returns (uint256) {
        uint256 start = roundTransferStart[round];
        if (start == 0) return 0; // not opened yet
        uint256 elapsed = block.timestamp - start;
        if (elapsed >= TRANSFER_WINDOW) return 0;
        return TRANSFER_WINDOW - elapsed;
    }

    /// @notice Whether a round's 60-min transfer window is currently open.
    function isTransferWindowOpen(uint256 round) public view returns (bool) {
        return transferWindowRemaining(round) > 0;
    }

    // Explicit trigger for keeper bots
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
        nextAvailableSlot++;
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

    // ─── Phase 3: EnergyTransfer ──────────────────────────────────────────────
    // 50 min on-chain phase. Actual transfer window is 60 min (overlaps next round by 10 min).
    // No on-chain logic needed here — window is enforced via roundTransferStart + TRANSFER_WINDOW.
}
