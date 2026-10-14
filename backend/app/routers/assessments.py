"""
Assessment endpoints with a built-in question bank for demo subjects.
"""
from __future__ import annotations

import json
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas, models

router = APIRouter(tags=["assessments"])

# ---------------------------------------------------------------------------
# Question Bank
# ---------------------------------------------------------------------------
QUESTION_BANK: Dict[str, List[Dict[str, Any]]] = {
    "CN101": [  # Computer Networks
        {
            "question_text": "Which layer of the OSI model is responsible for routing packets across networks?",
            "options": ["Data Link Layer", "Network Layer", "Transport Layer", "Session Layer"],
            "correct_answer": "Network Layer",
            "explanation": "The Network Layer (Layer 3) handles logical addressing and routing via protocols like IP.",
        },
        {
            "question_text": "What does TCP stand for?",
            "options": ["Transfer Control Protocol", "Transmission Control Protocol", "Transport Control Protocol", "Timed Control Protocol"],
            "correct_answer": "Transmission Control Protocol",
            "explanation": "TCP stands for Transmission Control Protocol, providing reliable, ordered delivery.",
        },
        {
            "question_text": "Which protocol is used to assign IP addresses automatically?",
            "options": ["DNS", "ARP", "DHCP", "ICMP"],
            "correct_answer": "DHCP",
            "explanation": "DHCP (Dynamic Host Configuration Protocol) dynamically assigns IP addresses to hosts.",
        },
        {
            "question_text": "What is the maximum segment size (MSS) in TCP?",
            "options": ["MTU minus IP header", "MTU minus IP and TCP headers", "1500 bytes always", "Negotiated at handshake only"],
            "correct_answer": "MTU minus IP and TCP headers",
            "explanation": "MSS = MTU - IP header (20 bytes) - TCP header (20 bytes), typically 1460 bytes on Ethernet.",
        },
        {
            "question_text": "Which protocol operates at the Application layer to resolve domain names to IP addresses?",
            "options": ["ARP", "DHCP", "DNS", "SNMP"],
            "correct_answer": "DNS",
            "explanation": "DNS (Domain Name System) translates human-readable domain names to IP addresses.",
        },
        {
            "question_text": "In CSMA/CD, what happens after a collision is detected?",
            "options": ["All stations stop forever", "Stations send jam signal then wait random backoff", "Priority station retransmits first", "Session is reset"],
            "correct_answer": "Stations send jam signal then wait random backoff",
            "explanation": "After collision, stations transmit a jam signal and use binary exponential backoff before retransmitting.",
        },
        {
            "question_text": "Which of the following is a connectionless protocol?",
            "options": ["TCP", "HTTP", "FTP", "UDP"],
            "correct_answer": "UDP",
            "explanation": "UDP (User Datagram Protocol) is connectionless — it sends datagrams without establishing a connection.",
        },
        {
            "question_text": "What is the purpose of the sliding window protocol?",
            "options": ["Error correction", "Flow control and pipeline transmission", "Routing optimization", "Address resolution"],
            "correct_answer": "Flow control and pipeline transmission",
            "explanation": "Sliding window allows multiple frames to be in transit simultaneously, improving throughput.",
        },
        {
            "question_text": "Which IP address class supports the most hosts per network?",
            "options": ["Class A", "Class B", "Class C", "Class D"],
            "correct_answer": "Class A",
            "explanation": "Class A has 24 bits for host addresses, supporting ~16 million hosts per network.",
        },
        {
            "question_text": "What does CIDR stand for?",
            "options": ["Classless Inter-Domain Routing", "Class Internet Domain Routing", "Classful Internet Data Routing", "Centralized Internet Domain Registry"],
            "correct_answer": "Classless Inter-Domain Routing",
            "explanation": "CIDR allows flexible allocation of IP address blocks without class constraints.",
        },
        {
            "question_text": "Which field in the IP header prevents packets from looping indefinitely?",
            "options": ["Checksum", "Protocol", "TTL", "Flags"],
            "correct_answer": "TTL",
            "explanation": "TTL (Time To Live) is decremented at each router; packet is dropped when TTL reaches 0.",
        },
        {
            "question_text": "What is a subnet mask of /24 in decimal?",
            "options": ["255.255.0.0", "255.255.255.0", "255.0.0.0", "255.255.255.128"],
            "correct_answer": "255.255.255.0",
            "explanation": "/24 means 24 bits set to 1: 11111111.11111111.11111111.00000000 = 255.255.255.0",
        },
        {
            "question_text": "Which protocol is used by routers to share routing information?",
            "options": ["ARP", "BGP", "ICMP", "SMTP"],
            "correct_answer": "BGP",
            "explanation": "BGP (Border Gateway Protocol) is the primary inter-domain routing protocol on the internet.",
        },
        {
            "question_text": "What is the purpose of the three-way handshake in TCP?",
            "options": ["Data transfer", "Connection establishment", "Connection termination", "Error recovery"],
            "correct_answer": "Connection establishment",
            "explanation": "TCP uses SYN, SYN-ACK, ACK to establish a reliable connection before data transfer.",
        },
        {
            "question_text": "Which layer is responsible for MAC addressing?",
            "options": ["Physical", "Data Link", "Network", "Transport"],
            "correct_answer": "Data Link",
            "explanation": "MAC addresses operate at the Data Link Layer (Layer 2) for local network delivery.",
        },
    ],
    "DS102": [  # Data Structures
        {
            "question_text": "What is the time complexity of searching in a balanced BST?",
            "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
            "correct_answer": "O(log n)",
            "explanation": "Balanced BST maintains O(log n) height, enabling O(log n) search.",
        },
        {
            "question_text": "Which data structure uses LIFO ordering?",
            "options": ["Queue", "Stack", "Linked List", "Deque"],
            "correct_answer": "Stack",
            "explanation": "Stack follows Last-In, First-Out (LIFO) — the last element pushed is the first popped.",
        },
        {
            "question_text": "What is the worst-case time complexity of QuickSort?",
            "options": ["O(n log n)", "O(n)", "O(n²)", "O(log n)"],
            "correct_answer": "O(n²)",
            "explanation": "QuickSort degrades to O(n²) when the pivot consistently divides the array poorly (e.g., sorted array).",
        },
        {
            "question_text": "Which traversal visits nodes in Left-Root-Right order?",
            "options": ["Preorder", "Postorder", "Inorder", "Level-order"],
            "correct_answer": "Inorder",
            "explanation": "Inorder traversal: Left → Root → Right. On a BST, it visits nodes in sorted order.",
        },
        {
            "question_text": "What is the space complexity of merge sort?",
            "options": ["O(1)", "O(log n)", "O(n)", "O(n²)"],
            "correct_answer": "O(n)",
            "explanation": "Merge sort requires O(n) auxiliary space for the temporary arrays during merging.",
        },
        {
            "question_text": "Which graph algorithm finds the shortest path from a single source in a weighted graph with no negative edges?",
            "options": ["BFS", "DFS", "Dijkstra's", "Bellman-Ford"],
            "correct_answer": "Dijkstra's",
            "explanation": "Dijkstra's algorithm uses a priority queue to find shortest paths efficiently in non-negative weighted graphs.",
        },
        {
            "question_text": "What is a heap property in a max-heap?",
            "options": ["Each parent ≤ children", "Each parent ≥ children", "Left child > right child", "Tree is perfectly balanced"],
            "correct_answer": "Each parent ≥ children",
            "explanation": "Max-heap property: every parent node has a value ≥ its children.",
        },
        {
            "question_text": "Which data structure is most efficient for implementing a priority queue?",
            "options": ["Array", "Linked List", "Heap", "Stack"],
            "correct_answer": "Heap",
            "explanation": "A binary heap provides O(log n) insert/delete-min with O(1) peek, ideal for priority queues.",
        },
        {
            "question_text": "What is the amortized time complexity of push in a dynamic array?",
            "options": ["O(n)", "O(log n)", "O(1)", "O(n²)"],
            "correct_answer": "O(1)",
            "explanation": "Though individual pushes can be O(n) during resize, amortized cost over n operations is O(1).",
        },
        {
            "question_text": "Which of the following sorting algorithms is stable?",
            "options": ["QuickSort", "HeapSort", "MergeSort", "Selection Sort"],
            "correct_answer": "MergeSort",
            "explanation": "MergeSort is stable — equal elements retain their original order.",
        },
        {
            "question_text": "What is the height of a complete binary tree with n nodes?",
            "options": ["n", "n/2", "⌊log₂n⌋", "2n"],
            "correct_answer": "⌊log₂n⌋",
            "explanation": "A complete binary tree with n nodes has height ⌊log₂n⌋.",
        },
        {
            "question_text": "Which graph representation is more space-efficient for sparse graphs?",
            "options": ["Adjacency Matrix", "Adjacency List", "Edge List only", "Incidence Matrix"],
            "correct_answer": "Adjacency List",
            "explanation": "Adjacency list uses O(V+E) space, while adjacency matrix always uses O(V²) space.",
        },
        {
            "question_text": "What is the purpose of hashing in data structures?",
            "options": ["Sorting elements", "O(1) average-case access", "Tree balancing", "Graph traversal"],
            "correct_answer": "O(1) average-case access",
            "explanation": "Hash functions map keys to array indices, enabling O(1) average-case insert/search/delete.",
        },
        {
            "question_text": "Which algorithm detects a cycle in a directed graph?",
            "options": ["BFS only", "DFS with visited/recursion stack", "Dijkstra's", "Kruskal's"],
            "correct_answer": "DFS with visited/recursion stack",
            "explanation": "DFS with a recursion stack tracks back-edges which indicate cycles in directed graphs.",
        },
        {
            "question_text": "What is the time complexity of building a heap from n elements?",
            "options": ["O(n log n)", "O(n)", "O(log n)", "O(n²)"],
            "correct_answer": "O(n)",
            "explanation": "Heapify-down from n/2 nodes takes O(n) total due to the geometric series of work at each level.",
        },
    ],
    "DB103": [  # Database Management
        {
            "question_text": "What does ACID stand for in database transactions?",
            "options": [
                "Atomicity, Consistency, Isolation, Durability",
                "Availability, Consistency, Integrity, Durability",
                "Atomicity, Concurrency, Isolation, Data-integrity",
                "Availability, Concurrency, Integrity, Distribution",
            ],
            "correct_answer": "Atomicity, Consistency, Isolation, Durability",
            "explanation": "ACID properties ensure reliable database transactions: Atomicity, Consistency, Isolation, Durability.",
        },
        {
            "question_text": "Which normal form eliminates partial dependencies?",
            "options": ["1NF", "2NF", "3NF", "BCNF"],
            "correct_answer": "2NF",
            "explanation": "2NF removes partial dependencies (non-key attributes depending on part of a composite key).",
        },
        {
            "question_text": "What is a foreign key?",
            "options": [
                "A key used in encryption",
                "A column referencing the primary key of another table",
                "A unique identifier for external tables",
                "The second candidate key",
            ],
            "correct_answer": "A column referencing the primary key of another table",
            "explanation": "A foreign key creates a referential link between two tables, enforcing referential integrity.",
        },
        {
            "question_text": "Which SQL clause filters groups after aggregation?",
            "options": ["WHERE", "HAVING", "GROUP BY", "ORDER BY"],
            "correct_answer": "HAVING",
            "explanation": "HAVING filters groups after GROUP BY aggregation; WHERE filters individual rows before grouping.",
        },
        {
            "question_text": "What type of join returns all rows from both tables with NULLs for unmatched rows?",
            "options": ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL OUTER JOIN"],
            "correct_answer": "FULL OUTER JOIN",
            "explanation": "FULL OUTER JOIN returns all rows from both tables; unmatched rows get NULL for the other table's columns.",
        },
        {
            "question_text": "What is a B+ tree index primarily used for?",
            "options": ["In-memory sorting", "Range queries and sequential access", "Hash-based lookup only", "Graph traversal"],
            "correct_answer": "Range queries and sequential access",
            "explanation": "B+ trees store all data in leaf nodes with a linked list, enabling efficient range scans.",
        },
        {
            "question_text": "What does normalization aim to achieve?",
            "options": [
                "Faster query execution",
                "Elimination of data redundancy and anomalies",
                "Maximizing storage usage",
                "Denormalization for reads",
            ],
            "correct_answer": "Elimination of data redundancy and anomalies",
            "explanation": "Normalization reduces redundancy and prevents update/insert/delete anomalies.",
        },
        {
            "question_text": "Which isolation level prevents dirty reads but allows non-repeatable reads?",
            "options": ["Read Uncommitted", "Read Committed", "Repeatable Read", "Serializable"],
            "correct_answer": "Read Committed",
            "explanation": "Read Committed prevents reading uncommitted data but allows non-repeatable reads within a transaction.",
        },
        {
            "question_text": "What is a view in SQL?",
            "options": [
                "A physical copy of a table",
                "A virtual table based on a query",
                "An index on multiple columns",
                "A stored procedure result",
            ],
            "correct_answer": "A virtual table based on a query",
            "explanation": "A view is a stored SQL query presented as a virtual table without physically storing data.",
        },
        {
            "question_text": "In ER modeling, what does a weak entity depend on?",
            "options": ["A derived attribute", "Its own primary key", "A strong entity's primary key", "A multi-valued attribute"],
            "correct_answer": "A strong entity's primary key",
            "explanation": "A weak entity has no primary key of its own and depends on a strong entity for identification.",
        },
        {
            "question_text": "What is a deadlock in databases?",
            "options": [
                "A query that never returns results",
                "Two transactions permanently blocking each other",
                "A corrupted index",
                "Failed transaction rollback",
            ],
            "correct_answer": "Two transactions permanently blocking each other",
            "explanation": "Deadlock occurs when two or more transactions wait for each other's locks indefinitely.",
        },
        {
            "question_text": "Which SQL command removes all rows from a table without logging individual row deletions?",
            "options": ["DELETE", "DROP", "TRUNCATE", "REMOVE"],
            "correct_answer": "TRUNCATE",
            "explanation": "TRUNCATE removes all rows quickly without logging each deletion; DROP removes the table structure too.",
        },
        {
            "question_text": "What is the purpose of a transaction log?",
            "options": ["Query caching", "Recovery and undo/redo operations", "Index maintenance", "User authentication"],
            "correct_answer": "Recovery and undo/redo operations",
            "explanation": "Transaction logs record all changes enabling rollback (undo) and crash recovery (redo).",
        },
        {
            "question_text": "Which of the following is NOT a DDL command?",
            "options": ["CREATE", "ALTER", "SELECT", "DROP"],
            "correct_answer": "SELECT",
            "explanation": "SELECT is a DML (Data Manipulation Language) command; CREATE, ALTER, DROP are DDL commands.",
        },
        {
            "question_text": "What is referential integrity?",
            "options": [
                "Data must be stored securely",
                "Foreign keys must reference existing primary keys",
                "All columns must have unique values",
                "Tables must be in 3NF",
            ],
            "correct_answer": "Foreign keys must reference existing primary keys",
            "explanation": "Referential integrity ensures foreign key values always reference valid primary key values.",
        },
    ],
    "OS104": [  # Operating Systems
        {
            "question_text": "What is the purpose of a context switch?",
            "options": [
                "Switching between user modes",
                "Saving/restoring CPU state when switching processes",
                "Changing memory allocation",
                "Switching between kernel versions",
            ],
            "correct_answer": "Saving/restoring CPU state when switching processes",
            "explanation": "A context switch saves the current process state (registers, PC) and loads the next process's state.",
        },
        {
            "question_text": "Which page replacement algorithm suffers from Belady's Anomaly?",
            "options": ["LRU", "Optimal", "FIFO", "Clock"],
            "correct_answer": "FIFO",
            "explanation": "FIFO can have more page faults with more frames (Belady's Anomaly); LRU and Optimal are stack algorithms.",
        },
        {
            "question_text": "What is thrashing in virtual memory?",
            "options": [
                "Excessive swapping causing negligible CPU utilization",
                "Fragmentation of disk space",
                "Cache invalidation",
                "High CPU utilization with no I/O",
            ],
            "correct_answer": "Excessive swapping causing negligible CPU utilization",
            "explanation": "Thrashing occurs when processes spend more time swapping pages than executing, collapsing CPU utilization.",
        },
        {
            "question_text": "Which scheduling algorithm minimizes average waiting time for a set of known burst times?",
            "options": ["FCFS", "Round Robin", "SJF", "Priority"],
            "correct_answer": "SJF",
            "explanation": "Shortest Job First (non-preemptive) minimizes average waiting time when all burst times are known.",
        },
        {
            "question_text": "What is a semaphore?",
            "options": [
                "A hardware interrupt signal",
                "A synchronization primitive for mutual exclusion",
                "A memory segment identifier",
                "A network socket abstraction",
            ],
            "correct_answer": "A synchronization primitive for mutual exclusion",
            "explanation": "Semaphores are integer variables used for process synchronization via wait (P) and signal (V) operations.",
        },
        {
            "question_text": "Which of the following is NOT a necessary condition for deadlock?",
            "options": ["Mutual Exclusion", "Preemption", "Hold and Wait", "Circular Wait"],
            "correct_answer": "Preemption",
            "explanation": "The four Coffman conditions for deadlock are Mutual Exclusion, Hold & Wait, No Preemption, and Circular Wait.",
        },
        {
            "question_text": "What is the main advantage of paging over segmentation?",
            "options": [
                "Logical grouping of memory",
                "Eliminates external fragmentation",
                "Faster access time",
                "Smaller page tables",
            ],
            "correct_answer": "Eliminates external fragmentation",
            "explanation": "Paging uses fixed-size frames, eliminating external fragmentation (though internal fragmentation can occur).",
        },
        {
            "question_text": "What is a process control block (PCB)?",
            "options": [
                "A CPU instruction buffer",
                "OS data structure storing process state and metadata",
                "A disk partition control record",
                "A memory page descriptor",
            ],
            "correct_answer": "OS data structure storing process state and metadata",
            "explanation": "PCB stores process state, CPU registers, memory info, I/O status, and scheduling information.",
        },
        {
            "question_text": "Which memory allocation strategy avoids external fragmentation completely?",
            "options": ["First Fit", "Best Fit", "Paging", "Worst Fit"],
            "correct_answer": "Paging",
            "explanation": "Paging uses fixed-size blocks eliminating external fragmentation; contiguous allocation strategies suffer from it.",
        },
        {
            "question_text": "What does the TLB (Translation Lookaside Buffer) do?",
            "options": [
                "Stores recently used disk blocks",
                "Caches recent virtual-to-physical address translations",
                "Buffers network packets",
                "Stores process control blocks",
            ],
            "correct_answer": "Caches recent virtual-to-physical address translations",
            "explanation": "TLB is a fast hardware cache for page table entries, reducing the cost of virtual address translation.",
        },
        {
            "question_text": "In the producer-consumer problem, what prevents the producer from overwriting unread data?",
            "options": ["Mutex only", "Full semaphore", "Empty semaphore", "Spinlock"],
            "correct_answer": "Full semaphore",
            "explanation": "The 'full' semaphore tracks filled buffer slots; producer waits on 'empty' and consumer waits on 'full'.",
        },
        {
            "question_text": "Which of the following is a kernel-level thread advantage over user-level threads?",
            "options": [
                "Faster thread creation",
                "Blocking system calls don't block the whole process",
                "No OS involvement",
                "Portable across OS types",
            ],
            "correct_answer": "Blocking system calls don't block the whole process",
            "explanation": "Kernel threads allow other threads to run when one blocks on I/O; user-level threads all block together.",
        },
        {
            "question_text": "What is the working set model used for?",
            "options": [
                "Disk scheduling",
                "Determining the set of pages a process actively uses",
                "CPU scheduling",
                "File system organization",
            ],
            "correct_answer": "Determining the set of pages a process actively uses",
            "explanation": "Working set W(t,Δ) is the set of pages referenced in the last Δ time units, used to guide page allocation.",
        },
        {
            "question_text": "Which disk scheduling algorithm is fairest for all requests?",
            "options": ["SSTF", "FCFS", "SCAN", "C-SCAN"],
            "correct_answer": "FCFS",
            "explanation": "FCFS serves requests in order of arrival, ensuring no request is starved, though not optimal for throughput.",
        },
        {
            "question_text": "What is a zombie process?",
            "options": [
                "A process consuming 100% CPU",
                "A terminated process whose entry remains in the process table",
                "A sleeping process that can't wake",
                "A process without a parent",
            ],
            "correct_answer": "A terminated process whose entry remains in the process table",
            "explanation": "A zombie process has finished executing but its PCB remains until the parent calls wait() to collect exit status.",
        },
    ],
}

# Generic fallback questions
GENERIC_QUESTIONS: List[Dict[str, Any]] = [
    {
        "question_text": "What is the primary purpose of an operating system?",
        "options": ["Run applications directly", "Manage hardware and provide services to programs", "Store files on disk", "Provide internet access"],
        "correct_answer": "Manage hardware and provide services to programs",
        "explanation": "The OS is an intermediary between hardware and user applications.",
    },
    {
        "question_text": "Which data structure is used for implementing recursion?",
        "options": ["Queue", "Tree", "Stack", "Hash Table"],
        "correct_answer": "Stack",
        "explanation": "Function call stacks use LIFO ordering — the same as a stack data structure.",
    },
]


def _get_questions_for_subject(subject_code: Optional[str], n: int) -> List[Dict[str, Any]]:
    """Pull n questions from the bank for the given subject code."""
    bank = QUESTION_BANK.get(subject_code or "", GENERIC_QUESTIONS)
    if len(bank) < n:
        bank = bank + GENERIC_QUESTIONS
    return random.sample(bank, min(n, len(bank)))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/api/assessments/start", status_code=status.HTTP_201_CREATED)
def start_assessment(req: schemas.AssessmentStartRequest, db: Session = Depends(get_db)):
    """Create a new assessment with questions from the question bank."""
    student = crud.get_student(db, req.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    subject_code = None
    if req.subject_id:
        subject = crud.get_subject(db, req.subject_id)
        if subject:
            subject_code = subject.code

    # Create the assessment record
    assessment = models.Assessment(
        student_id=req.student_id,
        subject_id=req.subject_id,
        topic_id=req.topic_id,
        total_questions=req.num_questions,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    # Select questions
    raw_questions = _get_questions_for_subject(subject_code, req.num_questions)
    question_records = []
    for q in raw_questions:
        opts = q.get("options", [])
        aq = models.AssessmentQuestion(
            assessment_id=assessment.id,
            question_text=q["question_text"],
            options_json=json.dumps(opts),
            correct_answer=q["correct_answer"],
            explanation=q.get("explanation"),
        )
        db.add(aq)
        question_records.append(aq)

    db.commit()
    for aq in question_records:
        db.refresh(aq)

    crud.log_activity(db, req.student_id, "assessment_started", f"Assessment {assessment.id} started.")

    return {
        "assessment_id": assessment.id,
        "total_questions": assessment.total_questions,
        "questions": [
            {
                "id": aq.id,
                "question_text": aq.question_text,
                "options": json.loads(aq.options_json) if aq.options_json else [],
            }
            for aq in question_records
        ],
    }


@router.post("/api/assessments/{assessment_id}/submit")
def submit_assessment(
    assessment_id: int,
    req: schemas.AssessmentSubmitRequest,
    db: Session = Depends(get_db),
):
    """Submit answers, score the assessment, and update topic mastery."""
    assessment = crud.get_assessment(db, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.completed_at:
        raise HTTPException(status_code=400, detail="Assessment already submitted")

    # Build answer lookup
    answer_map = {a.question_id: a.student_answer for a in req.answers}

    correct_count = 0
    total = 0
    questions = db.query(models.AssessmentQuestion).filter(
        models.AssessmentQuestion.assessment_id == assessment_id
    ).all()

    for q in questions:
        student_answer = answer_map.get(q.id)
        if student_answer is not None:
            q.student_answer = student_answer
            q.is_correct = student_answer.strip().lower() == q.correct_answer.strip().lower()
            if q.is_correct:
                correct_count += 1
        total += 1

    db.commit()

    # Update assessment
    assessment.score = correct_count
    assessment.total_questions = total
    assessment.completed_at = datetime.utcnow()
    db.commit()

    # Update topic mastery if topic_id set
    if assessment.topic_id and total > 0:
        score_ratio = correct_count / total
        topic = crud.get_topic(db, assessment.topic_id)
        if topic:
            if topic.mastery_estimate is not None:
                new_mastery = (topic.mastery_estimate * 0.5) + (score_ratio * 0.5)
            else:
                new_mastery = score_ratio
            update = schemas.TopicUpdate(
                mastery_estimate=round(new_mastery, 4),
                last_studied_at=datetime.utcnow(),
            )
            crud.update_topic(db, assessment.topic_id, update)

    crud.log_activity(
        db, assessment.student_id, "assessment_completed",
        f"Assessment {assessment_id}: {correct_count}/{total} correct."
    )

    percentage = round((correct_count / total * 100), 1) if total else 0
    return {
        "assessment_id": assessment_id,
        "score": correct_count,
        "total_questions": total,
        "percentage": percentage,
        "grade": "A" if percentage >= 90 else "B" if percentage >= 75 else "C" if percentage >= 60 else "D" if percentage >= 50 else "F",
        "results": [
            {
                "question_id": q.id,
                "question_text": q.question_text,
                "correct_answer": q.correct_answer,
                "student_answer": q.student_answer,
                "is_correct": q.is_correct,
                "explanation": q.explanation,
            }
            for q in questions
        ],
    }


@router.get("/api/assessments/history")
def assessment_history(student_id: int = 1, db: Session = Depends(get_db)):
    """Get assessment history for a student."""
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    assessments = crud.get_assessments_by_student(db, student_id)
    return [
        {
            "id": a.id,
            "subject_id": a.subject_id,
            "topic_id": a.topic_id,
            "score": a.score,
            "total_questions": a.total_questions,
            "percentage": round(a.score / a.total_questions * 100, 1) if a.total_questions and a.score is not None else None,
            "completed_at": a.completed_at.isoformat() if a.completed_at else None,
            "duration_minutes": a.duration_minutes,
        }
        for a in assessments
    ]


@router.get("/api/assessments/{assessment_id}")
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """Get a specific assessment with all questions and answers."""
    assessment = crud.get_assessment(db, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    return {
        "id": assessment.id,
        "student_id": assessment.student_id,
        "subject_id": assessment.subject_id,
        "topic_id": assessment.topic_id,
        "score": assessment.score,
        "total_questions": assessment.total_questions,
        "percentage": round(assessment.score / assessment.total_questions * 100, 1)
        if assessment.total_questions and assessment.score is not None else None,
        "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
        "questions": [
            {
                "id": q.id,
                "question_text": q.question_text,
                "options": json.loads(q.options_json) if q.options_json else [],
                "correct_answer": q.correct_answer if assessment.completed_at else None,
                "student_answer": q.student_answer,
                "is_correct": q.is_correct,
                "explanation": q.explanation if assessment.completed_at else None,
            }
            for q in assessment.questions
        ],
    }
