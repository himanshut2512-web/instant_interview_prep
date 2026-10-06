from ._build import P, Q, S, T, md, note

TOPIC = {
    "key": "dsa",
    "name": "Data Structures & Algorithms",
    "keywords": ["data structures", "data structures and algorithms", "dsa", "leetcode", "coding round",
                 "coding rounds", "software engineer", "software development", "sde", "developer", "programming",
                 "java", "c++", "competitive programming"],
    "core": ["data structures", "dsa", "leetcode", "coding round", "coding rounds", "software engineer"],
    "subtopics": ["Complexity analysis", "Arrays, strings & hashing", "Two pointers & sliding window",
                  "Stacks, queues & heaps", "Trees & graphs (BFS/DFS)", "Binary search", "Dynamic programming"],
    "revision": note(
        summary="Coding rounds assess problem-solving under time pressure: clarify, pick the right data structure, "
        "reason about complexity, write clean code and test it. Most problems map to a handful of patterns.",
        concepts=[
            ("Big-O", "How time/space grow with input size: O(1) < O(log n) < O(n) < O(n log n) < O(n^2) < O(2^n)."),
            ("Hash map", "O(1) average insert/lookup - counting, de-duplication, complement lookups (two-sum)."),
            ("Two pointers", "Walk from both ends or at two speeds - sorted pair sums, removing duplicates, cycles."),
            ("Sliding window", "Maintain a window over a sequence - longest/shortest subarray or substring problems."),
            ("Stack / queue", "LIFO for matching brackets, monotonic stacks; FIFO for BFS and scheduling."),
            ("Heap", "O(log n) push/pop of min/max - top-k, merging sorted lists, scheduling."),
            ("Binary search", "Halve the search space on sorted data or a monotonic condition - O(log n)."),
            ("BFS / DFS", "Level-order shortest paths in unweighted graphs / exhaustive exploration, recursion."),
            ("Dynamic programming", "Overlapping subproblems + optimal substructure; memoise or tabulate."),
            ("Recursion", "Base case + reduction; watch stack depth."),
        ],
        explanation=md("""
            **A repeatable interview method.**
            1. **Clarify**: input size, constraints, edge cases, expected output, duplicates, negative numbers.
            2. **Examples**: work one small example by hand.
            3. **Brute force first**, state its complexity, then optimise.
            4. **Pick a pattern** (table below) and explain the idea before coding.
            5. **Code** cleanly with good names; narrate.
            6. **Test** with your example and edge cases; state final complexity.

            | Signal in the problem | Pattern |
            |---|---|
            | "pair/complement", "seen before", counts | Hash map / set |
            | Sorted array, pair with target | Two pointers |
            | Contiguous subarray/substring, "longest/shortest" | Sliding window |
            | "k largest/smallest", streaming top-k | Heap |
            | Sorted data or monotonic yes/no condition | Binary search |
            | Matching brackets, "next greater element" | Stack / monotonic stack |
            | Shortest path in unweighted graph, levels | BFS |
            | All paths/combinations, connected components | DFS / backtracking |
            | "number of ways", "min cost", overlapping subproblems | Dynamic programming |
            | Intervals / meetings | Sort by start, sweep |

            **Complexity talk.** Always state time and space, e.g. "O(n) time with one pass and O(n) space for the
            hash map". Know that sorting is O(n log n) and that Python's `in` on a list is O(n).
        """),
        code=md("""
            def length_of_longest_unique_substring(s: str) -> int:
                # sliding window: expand right, shrink left when a duplicate appears
                last_seen, left, best = {}, 0, 0
                for right, ch in enumerate(s):
                    if ch in last_seen and last_seen[ch] >= left:
                        left = last_seen[ch] + 1
                    last_seen[ch] = right
                    best = max(best, right - left + 1)
                return best

            assert length_of_longest_unique_substring("abcabcbb") == 3
            assert length_of_longest_unique_substring("") == 0
        """),
        language="python",
        pitfalls=[
            "Coding immediately without clarifying constraints and edge cases.",
            "Off-by-one errors in loops, windows and binary search bounds.",
            "Forgetting the empty input, single element and duplicate cases.",
            "Not stating time and space complexity.",
            "Mutating input unexpectedly or using recursion too deep for Python's default limit.",
        ],
        tips=[
            "Think aloud - interviewers grade the process, not just the final code.",
            "Start with brute force, then improve - a correct O(n^2) beats a broken O(n).",
            "Write small helper functions and test with a quick dry run.",
            "If stuck, revisit the pattern table and the constraints (n <= 10^5 means about O(n log n)).",
        ],
        cheat_sheet=[
            "n <= 10^5 -> aim for O(n log n) or better; n <= 20 -> exponential may be fine.",
            "Binary search template: while lo <= hi: mid = (lo + hi) // 2.",
            "heapq is a min-heap; push negatives for a max-heap.",
            "BFS uses collections.deque; mark visited when enqueuing.",
            "DP: define state, transition, base case, order of evaluation.",
            "Recursion depth limit in Python is about 1000 by default.",
        ],
        likely_questions=[
            "Two Sum", "Valid Parentheses", "Longest substring without repeating characters",
            "Merge intervals", "Kth largest element", "Number of islands", "Climbing stairs / coin change",
        ],
    ),
    "theory": [
        T("beginner", "What is Big-O notation and why does it matter? Give examples of common complexities.",
          """
          Big-O describes how an algorithm's running time or memory grows as the input size n grows, ignoring
          constants - it tells us how a solution will **scale**.

          | Complexity | Example |
          |---|---|
          | O(1) | dict/set lookup, array index access |
          | O(log n) | binary search, heap push/pop |
          | O(n) | single pass over a list, linear search |
          | O(n log n) | efficient sorting (merge sort, Timsort) |
          | O(n^2) | nested loops comparing all pairs |
          | O(2^n) | generating all subsets |

          Why it matters: an O(n^2) solution is fine for 1,000 items (1M operations) but painful for 1M items
          (10^12). In interviews, I state the brute-force complexity, then optimise - e.g. two-sum from O(n^2)
          nested loops to O(n) with a hash map. Space complexity matters too, especially for large data.
          """,
          ["Definition (growth rate)", "Common classes with examples", "Why scaling matters", "Space complexity too"],
          "Use the two-sum O(n^2) -> O(n) example; it shows you apply the idea.",
          ["What is amortised complexity?", "Best vs average vs worst case?"], hot=True),
        T("beginner", "When would you use an array/list vs a hash map vs a set vs a heap?",
          """
          - **Array/list**: ordered data, index access O(1), iteration, appending at the end. Searching for a value
            is O(n).
          - **Hash map (dict)**: key -> value lookups in O(1) average - counting frequencies, caching, mapping ids
            to records, finding complements.
          - **Set**: membership tests and de-duplication in O(1) average.
          - **Heap (priority queue)**: repeatedly get the smallest/largest element in O(log n) - top-k, scheduling,
            Dijkstra, merging sorted streams.
          - Also: **deque** for queues/BFS (O(1) at both ends), **stack** for nested structures and undo operations.

          Choosing the right structure is often the whole trick: e.g. "find duplicates" becomes trivial with a set.
          """,
          ["Operations & complexities", "Use case per structure", "Deque/stack mention"],
          "Pick one problem and show how the structure choice changes its complexity.",
          ["How does a hash map handle collisions?", "Why is a heap better than sorting for top-k?"], hot=True),
        T("intermediate", "Explain the two-pointer and sliding-window techniques with examples.",
          """
          **Two pointers**: keep two indices that move based on a condition, avoiding nested loops.
          - Sorted array, find a pair summing to a target: `left` at start, `right` at end; move `left` up if the
            sum is too small, `right` down if too large - O(n).
          - Fast/slow pointers detect cycles in linked lists.

          **Sliding window**: maintain a contiguous window `[left, right]` over an array/string and update a running
          state as the window expands or shrinks.
          - Fixed size: maximum sum of any k consecutive elements - add the new element, subtract the outgoing one.
          - Variable size: longest substring without repeating characters - expand `right`, and move `left` past
            the previous occurrence when a duplicate appears.

          Both turn O(n^2) brute force into O(n) because each pointer moves at most n times.
          """,
          ["Two-pointer mechanics", "Sliding window fixed vs variable", "Why it's O(n)", "Examples"],
          "Mention the signal words that suggest each pattern (sorted, contiguous, longest/shortest).",
          ["How would you find the smallest subarray with sum >= target?", "How do you detect a cycle in a linked list?"]),
        T("intermediate", "What is the difference between BFS and DFS, and when do you use each?",
          """
          - **BFS** explores level by level using a **queue**. It finds the **shortest path in an unweighted graph**
            and is used for level-order traversal, nearest-neighbour searches and "minimum number of steps" problems.
            Memory can grow with the width of the graph.
          - **DFS** goes deep along one path before backtracking, using **recursion or a stack**. It suits
            exhaustive exploration: connected components, cycle detection, topological sort, path existence,
            backtracking (permutations, subsets).

          Both are O(V + E) time with a visited set. Example: "number of islands" works with either - DFS flood-fill
          is shorter to write; BFS avoids deep recursion on huge grids.
          """,
          ["Queue vs stack/recursion", "Shortest path property of BFS", "Typical DFS uses", "Complexity O(V+E)"],
          "Name a concrete problem for each and mention Python's recursion limit as a practical concern.",
          ["How would you find the shortest path in a weighted graph?", "How do you detect a cycle in a directed graph?"],
          hot=True),
        T("advanced", "How do you recognise and solve a dynamic programming problem?",
          """
          DP applies when a problem has **optimal substructure** (the optimal answer is built from optimal answers to
          subproblems) and **overlapping subproblems** (the same subproblems recur). Signals: "number of ways",
          "minimum/maximum cost", "can we reach", choices at each step.

          Recipe:
          1. **State**: what does `dp[i]` (or `dp[i][j]`) mean? e.g. min coins to make amount i.
          2. **Transition**: how is it computed from smaller states? `dp[i] = min(dp[i - c] + 1 for c in coins)`.
          3. **Base cases**: `dp[0] = 0`.
          4. **Order**: compute small to large (tabulation) or recurse with memoisation (`@lru_cache`).
          5. **Answer & complexity**: e.g. O(amount x coins) time, O(amount) space; optimise space if only the
             previous row is needed.

          Classic problems: climbing stairs, coin change, longest common subsequence, knapsack, edit distance,
          longest increasing subsequence.
          """,
          ["Two properties", "State/transition/base/order recipe", "Memoisation vs tabulation", "Classic examples"],
          "Solve a tiny instance by hand to discover the recurrence - interviewers appreciate the process.",
          ["Top-down vs bottom-up?", "How would you reconstruct the actual solution, not just the value?"]),
        T("advanced", "How does a hash map work internally, and what is its worst-case complexity?",
          """
          A hash map stores key-value pairs in an array of buckets. A **hash function** maps each key to an index;
          lookups compute the hash and go straight to that slot - O(1) on average.

          **Collisions** (two keys mapping to the same slot) are resolved by **chaining** (each bucket holds a small
          list) or **open addressing** (probe for the next free slot; Python's dict uses open addressing with
          perturbed probing). When the load factor gets too high, the table **resizes** (allocate a bigger array and
          rehash everything) - an O(n) operation, but amortised O(1) per insert.

          Worst case is **O(n)** when many keys collide (poor hash function or adversarial input). Keys must be
          **hashable and immutable** so their hash doesn't change - that's why lists can't be dict keys.
          Python dicts also preserve insertion order (3.7+).
          """,
          ["Hashing to buckets", "Collision strategies", "Resizing & amortised cost", "Worst case and hashability"],
          "Mention amortised analysis for resizing - a mark of depth.",
          ["What is a good hash function?", "Why must keys be immutable?"]),
    ],
    "practical": [
        P("beginner", "Two Sum: return the indices of the two numbers that add up to a target.",
          """
          `nums = [2, 7, 11, 15]`, `target = 9` -> `[0, 1]`. Exactly one solution exists; don't use the same element
          twice.
          """,
          ["Brute force O(n^2): check all pairs.", "Optimise: store seen values in a dict value -> index.",
           "For each number, check whether target - num was seen.", "Return indices when found."],
          "One pass with a hash map: for each element, its complement either appeared earlier (found) or we record "
          "the element for later. O(n) time, O(n) space.",
          """
          def two_sum(nums, target):
              seen = {}                       # value -> index
              for i, num in enumerate(nums):
                  complement = target - num
                  if complement in seen:
                      return [seen[complement], i]
                  seen[num] = i
              return []

          assert two_sum([2, 7, 11, 15], 9) == [0, 1]
          assert two_sum([3, 3], 6) == [0, 1]
          """, "python",
          "O(n) time, O(n) space.",
          ["Duplicate values ([3, 3])", "Negative numbers", "No valid pair (return empty or raise)"],
          "Mention the brute-force complexity first, then the improvement - the expected flow.",
          ["What if the array is sorted?", "Return all unique pairs instead?"], hot=True),
        P("intermediate", "Merge overlapping intervals.",
          """
          `intervals = [[1, 3], [2, 6], [8, 10], [15, 18]]` -> `[[1, 6], [8, 10], [15, 18]]`.
          """,
          ["Sort intervals by start.", "Keep a result list; compare each interval with the last merged one.",
           "Overlap if start <= last end: extend the end.", "Otherwise append a new interval."],
          "After sorting by start, overlapping intervals are adjacent, so a single sweep merges them.",
          """
          def merge(intervals):
              if not intervals:
                  return []
              intervals = sorted(intervals, key=lambda x: x[0])
              merged = [intervals[0][:]]
              for start, end in intervals[1:]:
                  if start <= merged[-1][1]:
                      merged[-1][1] = max(merged[-1][1], end)
                  else:
                      merged.append([start, end])
              return merged

          assert merge([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
          assert merge([[1, 4], [4, 5]]) == [[1, 5]]
          """, "python",
          "O(n log n) for sorting, O(n) for the sweep; O(n) output space.",
          ["Touching intervals [1,4],[4,5]", "Fully contained intervals", "Unsorted input", "Empty list"],
          "Ask whether touching intervals count as overlapping before coding.",
          ["Insert a new interval into a sorted list?", "Minimum meeting rooms needed?"], hot=True),
        P("advanced", "Number of islands: count connected groups of '1's in a 2D grid.",
          """
          ```
          grid = [["1","1","0","0"],
                  ["1","0","0","1"],
                  ["0","0","1","1"]]
          ```
          Output: `2`. Cells connect horizontally and vertically.
          """,
          ["Scan every cell.", "When a land cell is found, count an island and flood-fill it.",
           "BFS with a deque avoids recursion-depth issues.", "Mark visited cells to avoid recounting."],
          "Each cell is visited a constant number of times, so the algorithm is linear in the grid size. BFS is "
          "safer than recursive DFS for very large grids in Python.",
          """
          from collections import deque

          def num_islands(grid):
              if not grid:
                  return 0
              rows, cols = len(grid), len(grid[0])
              seen = set()
              islands = 0
              for r in range(rows):
                  for c in range(cols):
                      if grid[r][c] == "1" and (r, c) not in seen:
                          islands += 1
                          queue = deque([(r, c)])
                          seen.add((r, c))
                          while queue:
                              x, y = queue.popleft()
                              for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                                  nx, ny = x + dx, y + dy
                                  if (0 <= nx < rows and 0 <= ny < cols
                                          and grid[nx][ny] == "1" and (nx, ny) not in seen):
                                      seen.add((nx, ny))
                                      queue.append((nx, ny))
              return islands
          """, "python",
          "O(rows x cols) time and space.",
          ["Empty grid", "All water / all land", "Very large grids (recursion depth)", "Diagonal adjacency rules"],
          "Explain why you mark cells as visited when enqueuing, not when dequeuing.",
          ["Return the size of the largest island.", "How would you do it with union-find?"]),
    ],
    "scenario": [
        S("beginner", """
          In a live coding round you are given a problem you have never seen. After two minutes you still don't see
          an efficient solution, and the interviewer is quiet.
          """,
          "How do you handle the next 20 minutes?",
          [("Clarify", "Restate the problem, ask about constraints and edge cases."),
           ("Work an example", "Solve a small example by hand to expose structure."),
           ("Brute force", "State and possibly code a simple correct solution with its complexity."),
           ("Optimise", "Look for repeated work; map to known patterns; think aloud."),
           ("Test", "Dry-run with examples and edge cases; state final complexity.")],
          """
          I'd keep talking so the interviewer sees my reasoning. First I'd restate the problem and ask about input
          size and edge cases - constraints often hint at the target complexity.

          Then I'd work a small example by hand, which usually reveals the structure. I'd propose a brute-force
          solution out loud with its complexity, and if time allows, code it - a correct baseline is worth a lot.

          Next I'd look for repeated work in the brute force: can a hash map remove an inner loop? Is the input
          sortable for two pointers or binary search? Is there a recurrence for DP? I'd check in with the interviewer
          ("I'm thinking a sliding window could work because the subarray must be contiguous - does that sound
          reasonable?"), which often earns a hint. Finally I'd test with my example and edge cases and state the
          complexity.
          """,
          ["Communicates continuously", "Structured problem-solving", "Brute force before optimisation",
           "Uses hints productively", "Tests the code"],
          ["Going silent", "Jumping into code without a plan", "Giving up or asking for the answer"],
          ["How do you decide when to switch from brute force to optimising?"], hot=True),
        S("intermediate", """
          A teammate's function to find duplicate user records compares every record with every other one. It
          worked for 10,000 users, but with 2 million users it now runs for hours.
          """,
          "How would you improve it?",
          [("Analyse", "Pairwise comparison is O(n^2): 2M users means ~2 x 10^12 comparisons."),
           ("Normalise", "Define a normalised key (lower-case email, digits-only phone)."),
           ("Hash", "Group by key in a dictionary - O(n)."),
           ("Fuzzy matches", "Blocking + similarity only within blocks for near-duplicates."),
           ("Validate", "Compare results with the old method on a sample; measure runtime.")],
          """
          Comparing all pairs is O(n^2) - fine at 10k (50M comparisons) but about 2 trillion at 2M. The fix is to
          avoid pairwise comparison entirely for exact duplicates: build a **normalised key** per record (trimmed,
          lower-cased email; phone with digits only) and group records in a dictionary keyed by it. That's a single
          O(n) pass.

          For **fuzzy** duplicates (typos in names), use **blocking**: group records by a cheap key (e.g. same
          postcode + first letter of surname) and run the expensive similarity only within each block, which shrinks
          comparisons by orders of magnitude. At larger scale this maps naturally to a Spark groupBy.

          I'd validate on a sample against the old function's output and report the runtime improvement.
          """,
          ["Complexity reasoning with numbers", "Hashing on normalised keys", "Blocking for fuzzy matching",
           "Validation"],
          ["Micro-optimising the double loop", "Parallelising O(n^2) instead of fixing the algorithm",
           "Ignoring normalisation"],
          ["How would you choose a blocking key?", "How would you do this in SQL?"]),
        S("advanced", """
          You need to show the top 10 trending search terms of the last 60 minutes on a home page. Searches arrive
          at 20,000 per second, and the list must refresh every 10 seconds.
          """,
          "Which data structures and algorithm would you use?",
          [("Window", "Bucket counts per 10-second slot; keep 360 slots in a ring buffer."),
           ("Counting", "Hash map term -> count for the current window; subtract expiring slots."),
           ("Top-k", "Min-heap of size 10 over the counts, or approximate sketches."),
           ("Scale", "Count-Min Sketch + heavy-hitter algorithms if the vocabulary is huge."),
           ("Distribute", "Partition by term across workers, merge per-partition top-k.")],
          """
          I'd model the 60-minute sliding window as **360 buckets of 10 seconds** in a ring buffer. Each bucket holds
          a hash map of term counts. A global hash map holds the running total for the window: when a new bucket
          starts, I subtract the expiring bucket's counts and drop terms that reach zero.

          Every 10 seconds I compute the top 10 with a **min-heap of size 10** over the global counts - O(m log 10)
          for m distinct terms - or maintain it incrementally.

          If the vocabulary is enormous, exact counting uses too much memory, so I'd switch to a **Count-Min
          Sketch** for approximate counts plus a heavy-hitters structure (e.g. Space-Saving) to track candidates.
          At 20k events/s I'd partition terms by hash across workers (e.g. Kafka partitions), compute local top-k
          per partition and merge them - the global top 10 must appear among local top-k lists if k is chosen
          generously.
          """,
          ["Sliding window via buckets", "Hash map + heap for top-k", "Approximate algorithms at scale",
           "Distributed merge reasoning"],
          ["Sorting all terms every refresh", "Storing every raw event for an hour", "Ignoring memory limits"],
          ["How accurate is a Count-Min Sketch?", "Why is merging local top-k lists tricky?"]),
    ],
    "quiz": [
        Q("beginner", "What is the time complexity of binary search on a sorted array of n elements?",
          ["O(1)", "O(log n)", "O(n)", "O(n log n)"], 1,
          "Each step halves the remaining search space.",
          ["Only for direct index access.", "Correct.", "That's linear search.", "That's sorting."],
          "Mention that it requires sorted data or a monotonic condition.", hot=True),
        Q("beginner", "Which data structure gives O(1) average-time membership checks?",
          ["List", "Set", "Sorted list", "Linked list"], 1,
          "Sets are hash-based.",
          ["O(n).", "Correct.", "O(log n) with binary search.", "O(n)."],
          "Use sets for de-duplication and membership tests."),
        Q("intermediate", "Which structure is best for repeatedly retrieving the k largest items from a stream?",
          ["Stack", "Queue", "Min-heap of size k", "Unsorted list"], 2,
          "Keep a min-heap of the k largest seen so far; replace the root when a larger item arrives - O(log k).",
          ["LIFO, no ordering by value.", "FIFO, no ordering by value.", "Correct.", "Needs O(n) scans."],
          "Explain why a MIN-heap (not max) is used for the k LARGEST.", hot=True),
        Q("intermediate", "BFS on an unweighted graph is guaranteed to find:",
          ["The longest path", "The shortest path (fewest edges) from the source", "A topological order",
           "Strongly connected components"], 1,
          "BFS explores by distance layers, so the first time it reaches a node is via the fewest edges.",
          ["No.", "Correct.", "That's DFS-based (or Kahn's algorithm).", "Requires Tarjan/Kosaraju."],
          "For weighted graphs, switch to Dijkstra."),
        Q("advanced", "Two properties indicate a problem can be solved with dynamic programming:",
          ["Sorted input and unique values", "Optimal substructure and overlapping subproblems",
           "Greedy choice and small input", "Recursion and global variables"], 1,
          "DP reuses solutions of overlapping subproblems that combine into the optimal overall solution.",
          ["Unrelated.", "Correct.", "Greedy-choice property suggests a greedy algorithm instead.", "Not defining properties."],
          "Then describe state, transition, base case and order."),
    ],
}
