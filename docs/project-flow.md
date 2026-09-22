# Project flow

```
Company/Role → AI Voice Interview → Answer Analysis → Candidate Scoring
            → Role-Fit Engine → HR/Candidate Report → Hiring Decision (by a person)
```

## 1. Company, role and requirements
HR creates a role with the skills it needs. Each skill has an importance, the level
needed on day one (1–5), and whether it is critical. Four starter roles are included:
Software Engineer, Backend Developer, Data Engineer and UI/UX Designer.
HR then creates an interview link for a candidate.

## 2. AI voice interview
The candidate opens the link, agrees to AI assessment, and talks to an AssemblyAI
voice agent. The agent follows a fixed plan built from the role: an introduction,
questions on the top skills, a problem-solving scenario, a behavioural question, and
time for the candidate's questions. It ends the call itself when done.

## 3. Candidate answers
The browser records the text transcript of both sides. Audio is not stored.

## 4. AI analysis
Claude reads the transcript and the role requirements, and returns:
- a 1–5 score with evidence for technical knowledge, problem solving,
  communication and behavioural answers
- a 0–5 level with evidence for every skill used by any role
- strengths, weaknesses, improvement tips and a short summary

## 5. Score and feedback
The overall score is a weighted average of the four criteria (see
`docs/architecture.md` for the exact weights).

## 6. Role-fit analysis
The candidate's skill levels are compared with every role:
- ✅ Best-fit role
- 🟢 Suitable roles
- 🟡 Possible with training
- ❌ Not suitable roles

## 7. Hiring recommendation
Strongly recommend, Consider, Further interview or Not recommended, with the reasons
listed. It is advisory: a person on the hiring team makes the decision.

## 8. Reports
**HR gets** the score, criterion evidence, strengths, weaknesses, role fit for every
role, the recommendation with reasons, skill evidence and the full transcript.

**The candidate gets** their score, feedback, what to work on, skills to build for the
role, and other roles that match their skills. They don't see the hiring recommendation.

## Example
Candidate interviewed for Software Engineer. Overall score 82%.

| Role | Result |
|---|---|
| Software Engineer | Best fit |
| Backend Developer | Suitable |
| Data Engineer | Possible with training (Databases & SQL 2/4) |
| UI/UX Designer | Not suitable |
