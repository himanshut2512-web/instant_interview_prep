from ._build import P, Q, S, T, md, note

TOPIC = {
    "key": "behavioral",
    "name": "Behavioural & HR",
    "keywords": ["communication", "stakeholder", "stakeholders", "team", "leadership", "mentor", "collaboration",
                 "client", "ownership", "culture", "hr"],
    "always_include": True,
    "core": [],
    "subtopics": ["Tell me about yourself", "Why this company / role", "STAR stories", "Conflict & failure",
                  "Leadership & influence", "Strengths & weaknesses", "Salary & notice period", "Questions to ask"],
    "revision": note(
        summary="Behavioural and HR rounds decide between technically similar candidates. Interviewers look for "
        "ownership, communication, collaboration, learning from failure and genuine motivation - shown through "
        "specific, structured stories.",
        concepts=[
            ("STAR", "Situation (context), Task (your responsibility), Action (what YOU did - most of the answer), "
             "Result (quantified outcome + learning)."),
            ("Story bank", "6-8 reusable stories: success, failure, conflict, leadership, ambiguity, tight deadline, "
             "influencing, learning fast."),
            ("Tell me about yourself", "Present -> past -> future in 60-90 seconds, tailored to the role."),
            ("Why this company", "Specific: business, clients, projects, culture - linked to your experience and goals."),
            ("Weakness answer", "A real, non-critical weakness + concrete steps taken + evidence of improvement."),
            ("Conflict answer", "Focus on understanding the other view, data-driven resolution and a preserved relationship."),
            ("Failure answer", "Own it, explain the cause, what you changed afterwards."),
            ("Leadership without authority", "Influence through data, empathy, shared goals and small wins."),
            ("Reverse questions", "Ask about success in the first 90 days, team challenges, how work is evaluated."),
            ("Red flags", "Blaming others, vague 'we' answers, negativity about employers, no numbers."),
        ],
        explanation=md("""
            **How to build a STAR story** (60-120 seconds each):

            | Part | Share of time | Content |
            |---|---|---|
            | Situation | 10-15% | One or two sentences of context: team, project, stakes |
            | Task | 10% | Your specific responsibility or the problem to solve |
            | Action | 50-60% | What *you* did, step by step, including how you thought and dealt with people |
            | Result | 15-20% | Quantified outcome (%, time, money, users) + what you learned |

            **Mapping stories to common questions.** One strong project story can answer "biggest achievement",
            "difficult problem", "working under pressure" and "using data to influence". Prepare a grid of stories x
            competencies (ownership, teamwork, communication, leadership, adaptability, customer focus) so you can
            pick quickly in the interview.

            **Company fit.** Research the company's business lines, clients, recent news and values; prepare 2-3
            reasons you want *this* role that connect to your experience. For consulting/analytics firms, emphasise
            client communication, problem framing and delivering measurable business impact.

            **Delivery.** Use "I" for your actions, keep answers to about 2 minutes, pause for follow-ups, stay
            positive about past employers, and close with the result and learning.
        """),
        code=md("""
            STAR STORY TEMPLATE
            Title / competency:   e.g. "Fixed the forecasting pipeline - ownership under pressure"
            Situation:            Retail client, weekly forecasts feeding store replenishment...
            Task:                 I owned the model and the data pipeline...
            Action:               1) diagnosed ... 2) proposed ... 3) aligned with ... 4) implemented ...
            Result:               WAPE 31% -> 22%; stock-outs -9%; adopted for 1,200 stores
            Learning:             Now I add data-quality checks before every model release
            Questions it answers: achievement, difficult problem, pressure, impact
        """),
        language="text",
        pitfalls=[
            "Rambling context with little about your own actions.",
            "Saying 'we' throughout so your contribution is unclear.",
            "Fake weaknesses ('I'm a perfectionist') or blaming others in conflict stories.",
            "No numbers in results.",
            "Generic 'why this company' answers that could apply anywhere.",
        ],
        tips=[
            "Prepare and rehearse 6-8 STAR stories out loud; time them.",
            "Quantify results and add one line of learning.",
            "Tailor 'tell me about yourself' to the JD's top three requirements.",
            "Always have 3-4 thoughtful questions for the interviewer.",
        ],
        cheat_sheet=[
            "STAR = Situation, Task, Action, Result (+ Learning).",
            "Tell me about yourself: present role -> key past wins -> why this role next.",
            "Weakness: real + action plan + progress evidence.",
            "Salary: researched range, anchored on value; mention flexibility on total compensation.",
            "Leaving reason: forward-looking (growth, scope), never bitter.",
            "Close: reiterate interest and fit in one sentence.",
        ],
        likely_questions=[
            "Tell me about yourself.", "Why do you want to join us?", "Tell me about a conflict with a colleague.",
            "Describe a failure and what you learned.", "What is your greatest weakness?",
            "Where do you see yourself in five years?", "What are your salary expectations?",
        ],
    ),
    "theory": [
        T("beginner", "\"Tell me about yourself.\" How should you answer?",
          """
          Use **present -> past -> future** in 60-90 seconds, tailored to the role:

          1. **Present**: current role and the kind of problems you solve. "I'm a data scientist with 4 years of
             experience, currently building forecasting and churn models for retail clients."
          2. **Past**: two or three highlights that match the JD, with numbers. "I built a demand-forecasting system
             for 1,200 stores that cut forecast error from 31% to 22%, and a RAG assistant over 40k documents."
          3. **Future**: why this role is the logical next step. "I'm looking for a role where I work directly with
             clients on end-to-end AI solutions, which is why this position excites me."

          Keep it professional (no life story), end on the role, and pause - the interviewer will pick a thread to
          follow up on, so mention things you are happy to go deep on.
          """,
          ["Present-past-future structure", "Tailored to JD", "Quantified highlights", "Ends with motivation for role"],
          "Rehearse it until it sounds natural, not memorised - it sets the tone for the whole interview.",
          ["Walk me through your resume.", "What's the project you're proudest of?"], hot=True),
        T("beginner", "\"Why do you want to join our company?\"",
          """
          A strong answer has three parts:
          1. **Specific knowledge of the company**: its business, clients/domains, products or recent initiatives -
             something you could only say after research.
          2. **Fit with your experience**: how your skills match what they do ("You solve forecasting and pricing
             problems for retail and CPG clients - that's exactly what I've been doing for four years").
          3. **What you want to grow into**: the learning, scope or impact the role offers you.

          Avoid generic answers ("great culture, good brand, growth opportunities") and anything purely about
          compensation. Ending with enthusiasm for the specific team/role works well.
          """,
          ["Specific research", "Link to own experience", "Growth/impact motivation", "Avoid generic answers"],
          "Mention one concrete thing from your research (a case study, product, value) by name.",
          ["What do you know about our clients?", "Why not stay at your current company?"], hot=True),
        T("intermediate", "\"What is your greatest weakness?\"",
          """
          Pick a **real but non-critical** weakness, show **self-awareness**, and prove **improvement**:

          "Earlier in my career I found it hard to say no to ad-hoc requests from stakeholders, which sometimes
          delayed my main project. I started making trade-offs explicit - when a new request comes in, I share my
          current priorities and ask which should move. I also block focus time for deep work. In the last two
          quarters I delivered both major projects on time while still handling urgent requests, and my manager
          noted the improvement in my review."

          Avoid fake weaknesses ("perfectionism"), weaknesses central to the job (e.g. "I'm weak at SQL" for a data
          role), and stopping without an improvement plan.
          """,
          ["Genuine weakness", "Concrete actions", "Evidence of progress", "Not core to the role"],
          "Choose something believable and show measurable progress - honesty plus growth is what's assessed.",
          ["What feedback have you received from your manager?", "What are you working on improving now?"], hot=True),
        T("intermediate", "\"Why are you leaving your current job?\"",
          """
          Keep it **forward-looking and positive** - focus on what you're moving *towards*:
          - "I've learned a lot building models for one domain; I want broader exposure across industries and more
            client-facing work, which this role offers."
          - "I want to work on GenAI solutions end to end; my current role is mostly maintenance of existing models."

          Never criticise your manager or company, even if there were problems - interviewers worry you'll say the
          same about them. If there was a layoff or restructuring, say so briefly and factually, then pivot to what
          you're looking for.
          """,
          ["Forward-looking framing", "Ties to this role", "No negativity", "Handling layoffs factually"],
          "Have a one-sentence answer ready, then pivot to why this role fits.",
          ["What would make you stay at your current company?", "How long have you been looking?"], hot=True),
        T("advanced", "\"Where do you see yourself in five years?\"",
          """
          Show ambition that **aligns with the company's path**, plus commitment:

          "In five years I'd like to be leading end-to-end AI engagements - owning the solution design, guiding a
          small team of data scientists, and being a trusted advisor to client leadership. The next two or three
          years here would be about deepening my expertise in GenAI and MLOps and taking ownership of larger
          workstreams."

          Avoid answers that suggest you'll leave soon ("start my own company", "do an MBA abroad next year"),
          vagueness ("I'm not sure"), or targeting your interviewer's job in a way that sounds competitive.
          """,
          ["Ambition aligned with the role's growth path", "Shows commitment", "Concrete skills to build"],
          "Mention the company's career path if you know it (e.g. IC vs management track).",
          ["Do you prefer a technical or managerial track?", "What skills do you want to develop next?"]),
        T("advanced", "\"What are your salary expectations?\" How do you handle it?",
          """
          1. **Research** the market range for the role, level and city (salary portals, peers, recruiters).
          2. **Early in the process**, you can defer politely: "I'd like to understand the role and expectations
             better first; I'm sure we can agree on something fair if it's the right fit."
          3. **When pushed or at offer stage**, give a **researched range** with your target near the lower-middle
             to top: "Based on my experience and market data for similar roles, I'm looking at X to Y fixed."
          4. **Anchor on value**: tie the range to the impact you bring.
          5. **Consider total compensation**: fixed vs variable, joining bonus, ESOPs, notice-period buyout,
             learning budget, flexibility.
          6. Be honest about your current compensation if asked (in many places it's verified), and about notice
             period.

          Tone matters: confident, collaborative, never ultimatum-style.
          """,
          ["Market research", "Deferring vs giving a range", "Value anchoring", "Total compensation view",
           "Collaborative tone"],
          "Prepare your number in advance - hesitation weakens your position.",
          ["What is your notice period?", "Do you have other offers?"], hot=True),
    ],
    "practical": [
        P("beginner", "Build your STAR story bank: prepare six stories that cover the common behavioural themes.",
          """
          Themes to cover: (1) biggest achievement, (2) failure/mistake, (3) conflict, (4) leadership/initiative,
          (5) tight deadline/pressure, (6) influencing a stakeholder or client.
          """,
          ["List your 8-10 most significant projects/experiences.", "Map each to the competencies it shows.",
           "Write each in STAR form with numbers.", "Rehearse aloud; keep each under 2 minutes."],
          "One well-prepared story can answer several questions. A grid of stories x competencies lets you pick "
          "quickly and avoid repeating the same story to the same interviewer.",
          """
          | # | Story (title)                         | Achievement | Failure | Conflict | Leadership | Pressure | Influence |
          |---|---------------------------------------|:-----------:|:-------:|:--------:|:----------:|:--------:|:---------:|
          | 1 | Forecasting system for 1,200 stores    |      X      |         |          |     X      |    X     |           |
          | 2 | Model shipped with a data bug          |             |    X    |          |            |    X     |           |
          | 3 | Disagreement on metric definition       |             |         |    X     |            |          |     X     |
          | 4 | Mentored two junior analysts            |             |         |          |     X      |          |           |
          | 5 | Convinced client to run an A/B test     |      X      |         |          |            |          |     X     |
          | 6 | Delivered RAG POC in 3 weeks            |      X      |         |          |     X      |    X     |           |

          For each story: Situation (2 lines) / Task (1 line) / Action (4-6 bullets, "I") / Result (numbers) / Learning
          """, "markdown",
          "",
          ["Too few stories (repeating one)", "Stories without measurable results", "Stories that are too old"],
          "Bring your grid mentally into the interview - it reduces stress and improves answers.",
          ["Which story would you use for 'a time you went beyond your role'?"], hot=True),
        P("intermediate", "Write a tailored 60-90 second 'tell me about yourself' pitch for this job description.",
          """
          Use the JD's top three requirements and your resume. Structure: present -> past (2-3 matching highlights
          with numbers) -> future (why this role).
          """,
          ["Underline the JD's top 3 requirements.", "Pick resume highlights that prove each.",
           "Draft in present-past-future order.", "Cut to 150-200 words; rehearse and time it."],
          "Tailoring makes the interviewer immediately see the match. 150-200 spoken words is about 60-90 seconds.",
          """
          PRESENT  I'm a data scientist with 4 years of experience building forecasting, churn and GenAI solutions
                   for retail and CPG clients.
          PAST     At Northwind I built a demand-forecasting system for 1,200 stores that cut forecast error from
                   31% to 22% and reduced stock-outs by 9%. I also led a RAG assistant over 40,000 product documents
                   that reduced wrong answers by 35%, and I productionised models with MLflow and Azure ML.
          FUTURE   I'm now looking for a client-facing role where I can own AI solutions end to end - from framing
                   the business problem to deployment - which is exactly what this position is about.
          """, "text",
          "",
          ["Too long (over 2 minutes)", "Listing every job chronologically", "No link to the target role"],
          "Practise until it sounds conversational; end by handing the conversation back.",
          ["What would you change in this pitch for a managerial round?"]),
        P("advanced", "Prepare a 5-minute deep-dive narrative for your most important project.",
          """
          Interviewers often say "pick a project and walk me through it" and then probe for 20 minutes. Prepare a
          structured narrative and anticipate the follow-ups.
          """,
          ["Business problem and why it mattered (numbers).", "Your role and the team.",
           "Approach: data, methods, alternatives considered and why rejected.",
           "Challenges and trade-offs; how you validated.", "Impact, adoption and what you'd do differently."],
          "Interviewers test depth and ownership: why you chose each approach, what failed, how you measured "
          "impact. Preparing the 'alternatives considered' and 'what I'd change' parts shows senior thinking.",
          """
          1. Context      - client, problem, stakes ("INR 3 Cr annual churn losses")
          2. My role      - what I owned vs the team
          3. Data         - sources, volume, quality issues and how I fixed them
          4. Approach     - baseline -> model choices -> why (alternatives + trade-offs)
          5. Validation   - metrics, out-of-time tests, business validation
          6. Deployment   - how it ran in production, monitoring
          7. Impact       - numbers, adoption, stakeholder feedback
          8. Reflection   - what I'd do differently; what I learned
          Likely probes: "Why not deep learning?", "How did you handle leakage?", "What if data doubled?"
          """, "text",
          "",
          ["Not knowing details of parts you didn't own", "Claiming team results as your own", "No numbers"],
          "Draw a simple architecture diagram while you talk if a whiteboard is available.",
          ["What would you do with twice the time?", "What was the hardest technical decision?"], hot=True),
    ],
    "scenario": [
        S("beginner", """
          Interviewer: "Tell me about a time you disagreed with a teammate about how to approach a problem."
          """,
          "Answer using the STAR method.",
          [("Situation", "Briefly set the project context and the disagreement."),
           ("Task", "What you needed to achieve together."),
           ("Action", "Listen first, find the underlying concern, use data/experiment to decide, keep it respectful."),
           ("Result", "The outcome, quantified, and the relationship afterwards."),
           ("Learning", "What you now do differently.")],
          """
          **Situation**: On a churn project, a senior teammate wanted to use a deep-learning model, while I believed
          gradient boosting on our tabular data would be faster to deliver and easier to explain to the client.

          **Task**: We had four weeks to deliver a model the retention team could act on.

          **Action**: Instead of arguing in the meeting, I asked about his concern - he worried boosting would miss
          sequential usage patterns. That was fair, so I proposed a time-boxed comparison: two days each, same
          validation split and metrics. I also added sequence-based features (usage trends) to the boosting model to
          address his concern. We reviewed results together with our lead.

          **Result**: LightGBM matched the neural model's PR-AUC (0.41 vs 0.42) while training 20x faster and
          giving SHAP explanations the client valued, so we chose it - with his sequence features, which became the
          top predictors. We delivered a week early and still collaborate closely.

          **Learning**: When we disagree, I look for the concern behind the position and settle it with a quick,
          fair experiment.
          """,
          ["Respectful handling of disagreement", "Data-driven resolution", "Credits the other person",
           "Positive outcome and relationship"],
          ["Making the teammate look bad", "Escalating immediately", "A story where you simply gave in with no reasoning"],
          ["What if the experiment had favoured his approach?", "Tell me about a conflict with a manager."], hot=True),
        S("intermediate", """
          Interviewer: "Tell me about a time you made a mistake or failed. What did you learn?"
          """,
          "Answer using the STAR method.",
          [("Situation", "A real mistake with real consequences (not trivial)."),
           ("Task", "Your responsibility in it."),
           ("Action", "Own it quickly, contain the impact, communicate, fix the root cause."),
           ("Result", "How it was resolved; impact limited."),
           ("Learning", "The concrete change in how you work now.")],
          """
          **Situation**: I deployed an updated pricing-elasticity model for a retail client. A week later the
          category manager noticed recommended discounts were unusually deep for one category.

          **Task**: I owned the model release, so it was my responsibility to find and fix the issue.

          **Action**: I immediately told my manager and the client lead, and we paused recommendations for that
          category. Within a day I found the cause: a supplier feed had changed price units from rupees to paise for
          that category, and my pipeline had no range check, so elasticity estimates were distorted. I fixed the
          conversion, re-ran the model, and walked the client through what happened and what we changed.

          **Result**: Impact was limited to one week in one category, and the client appreciated the transparency -
          they extended the engagement the next quarter.

          **Learning**: I now add data-validation checks (ranges, units, distribution shifts) before any model release
          and have a peer review checklist for deployments. Those checks caught two upstream issues since.
          """,
          ["Owns the mistake honestly", "Fast containment and communication", "Root-cause fix",
           "Concrete, lasting learning"],
          ["A disguised success ('I worked too hard')", "Blaming others or the data team", "No learning"],
          ["How did the client react?", "What would you do if it happened again tomorrow?"], hot=True),
        S("advanced", """
          Interviewer: "Tell me about a time you had to convince senior stakeholders or a client to change direction
          when you had no authority over them."
          """,
          "Answer using the STAR method.",
          [("Situation", "Stakeholder position, stakes and why change was needed."),
           ("Task", "Your objective and constraints (no authority)."),
           ("Action", "Understand their goals, bring evidence, propose a low-risk test, build allies."),
           ("Result", "Decision changed; quantified business impact."),
           ("Learning", "Your influencing principles.")],
          """
          **Situation**: A client's marketing head wanted to send a retention offer to every customer our model
          flagged as likely to churn - about 200,000 people - which would have cost INR 1.6 Cr.

          **Task**: I believed many of those customers would stay anyway, so blanket offers would waste budget, but
          I had no authority over their campaign.

          **Action**: First I understood her goal: hit the quarterly retention target with confidence. Rather than
          challenging the plan, I showed data from a previous campaign where high-risk but highly engaged customers
          retained at the same rate with or without offers. I proposed a low-risk test: target the top-risk 60,000
          customers with offers and keep a randomised 10% holdout to measure true uplift. I aligned with her analytics
          lead beforehand so he could support the proposal in the meeting.

          **Result**: She agreed to the test. Offers drove a 4.2-point retention uplift for the targeted group, and
          the campaign cost 65% less than the original plan. The holdout design became their standard for campaigns.

          **Learning**: Influence works best when I anchor on their goal, bring evidence, and make the new path low
          risk to try.
          """,
          ["Understands the stakeholder's goals", "Evidence-based persuasion", "Low-risk experiment as a bridge",
           "Builds allies", "Quantified business outcome"],
          ["Winning by escalation", "Being condescending about the stakeholder's plan", "No measurable result"],
          ["What if she had refused?", "How do you handle a client who rejects your recommendation outright?"],
          hot=True),
    ],
    "quiz": [
        Q("beginner", "What does STAR stand for in behavioural interviews?",
          ["Strategy, Task, Analysis, Review", "Situation, Task, Action, Result", "Skills, Talent, Ambition, Results",
           "Situation, Thinking, Answer, Reflection"], 1,
          "STAR structures stories: context, your responsibility, your actions, and the measurable outcome.",
          ["Not the standard acronym.", "Correct.", "Not the standard acronym.", "Not the standard acronym."],
          "Add a final 'learning' line to stand out.", hot=True),
        Q("beginner", "Which is the best way to answer 'What is your greatest weakness?'",
          ["Say you have no weaknesses", "Give a fake weakness like perfectionism",
           "Share a real, non-critical weakness and how you're improving it", "Name a core skill for the job"], 2,
          "Interviewers look for self-awareness and growth.",
          ["Signals lack of self-awareness.", "Interviewers see through it.", "Correct.", "Disqualifies you."],
          "Include evidence of improvement."),
        Q("intermediate", "Which part of a STAR answer should take the most time?",
          ["Situation", "Task", "Action", "Result"], 2,
          "The Action shows what YOU did and how you think - it's what interviewers evaluate.",
          ["Keep context brief.", "Usually one sentence.", "Correct.", "Important but shorter."],
          "Use 'I' rather than 'we' in the Action part."),
        Q("intermediate", "At the end, the interviewer asks 'Do you have any questions for us?' The best response is:",
          ["No, everything is clear", "Ask about salary and leave policy only",
           "Ask thoughtful questions about the role, team, success criteria and challenges",
           "Ask how you performed in the interview"], 2,
          "Thoughtful questions show genuine interest and help you evaluate the role.",
          ["Signals low interest.", "Fine later, but not as your only questions.", "Correct.",
           "Puts the interviewer on the spot."],
          "Prepare 3-4 questions, e.g. 'What does success look like in the first 90 days?'", hot=True),
        Q("advanced", "Early in the process, a recruiter asks for your expected salary. A strong approach is:",
          ["Refuse to answer", "Give a researched range anchored on market data and your value, with flexibility on "
           "total compensation", "Ask for double your current salary", "Say 'whatever you think is fair'"], 1,
          "A researched range keeps you in the conversation while anchoring on value; flexibility on components "
          "keeps it collaborative.",
          ["Can stall the process.", "Correct.", "Unanchored and risky.", "Gives away your negotiating position."],
          "Know your number before the call."),
    ],
}
