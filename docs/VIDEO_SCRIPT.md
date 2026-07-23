# 7-Minute Video Script

Aim: 6 min 45 sec at natural speaking pace. Practice twice with a timer.
Pause a beat after each big claim. Keep your energy up on slides 7 and 8.

Total word count: ~940 words = about 6:45 at 140 wpm.

---

## Slide 1 - Title (0:00 to 0:25)

"Hi, I'm Esvanth Mohankumar, student number x-two-four-three-one-one-oh-seven-three.
For my H9IAPA CA I built an end-to-end automation of the recruitment intake
and shortlisting process at a fictional Dublin analytics firm called
Brightline Analytics. It combines a deterministic RPA layer with an agentic
AI layer running Llama three point three on Groq. Let me walk you through
what I built and how it works."

[Advance to slide 2]

---

## Slide 2 - The Problem (0:25 to 1:00)

"Why recruitment? Three numbers. Recruiters spend around twelve minutes per
applicant on manual work. Median time-to-shortlist for tech roles in Ireland
is over two weeks. And roughly seventy percent of recruiter time goes on
screening, not on actually engaging with candidates. The admin side of that
is a natural RPA fit. The screening side, which needs real judgement but is
pattern-driven, is a natural fit for agentic AI. That split is the whole
design."

[Advance to slide 3]

---

## Slide 3 - As-Is (1:00 to 1:45)

"This is the As-Is BPMN. Two lanes. HR Recruiter and Hiring Manager. The
recruiter publishes the advert, receives each application email, downloads
the CV, reads it, evaluates it against the JD, logs it to a tracker, scores
it, and forwards a shortlist. The manager either approves or bounces it back
for re-ranking. The pain points I identified are the ones you would expect.
Reading each CV takes real time. Scoring depends on who is doing it that
day. And there is no audit trail if someone later wants to check the process
was fair."

[Advance to slide 4]

---

## Slide 4 - To-Be (1:45 to 2:35)

"To-Be. I split the work into four lanes on purpose. The RPA Bot handles
everything deterministic. Poll the mailbox, extract the CV, parse the
metadata, store it, log it, and later send the approved emails through
SMTP. The AI Agent handles everything cognitive. Parse the CV to text,
score it against the JD using the LLM, produce structured JSON, draft the
personalised email, and push the ranked shortlist to the recruiter's
dashboard. HR Recruiter and Hiring Manager keep decision authority. And
that timer event on the RPA side handles the seven-day no-response
follow-up."

[Advance to slide 5]

---

## Slide 5 - Automation Potential (2:35 to 3:20)

"To decide what goes where I ran each task in the As-Is against four
criteria I pulled from the RPA literature. Rule regularity, data structure,
volume, and judgement intensity. Admin tasks go to RPA. Cognitive tasks go
to agentic AI. Manager decisions stay manual because they need to. Three
main risks I identified. Bias in scoring, schema drift in the LLM output,
and model drift over time. My mitigations are a strict Pydantic schema with
retry, a mandatory recruiter approval gate, and an audit log of everything."

[Advance to slide 6]

---

## Slide 6 - Architecture (3:20 to 3:55)

"Single Python codebase. The RPA layer reads from the mailbox and writes to
local storage. The agentic layer reads each CV, calls Groq with a structured
prompt, and writes a ranked JSON results file. The Streamlit dashboard sits
in front of the recruiter as the human-in-the-loop screen. Mock modes for
the inbox, the outbox, and even the LLM make the whole demo reproducible
without any real credentials, which is important for both testing and
academic honesty."

[Advance to slide 7. Optionally SWITCH to live dashboard here.]

---

## Slide 7 - Live Demo (3:55 to 5:00)

"Alright, here is the live pipeline running against six synthetic CVs I
generated on purpose across a range of quality. I'll click Run screening
pipeline in the sidebar. [PAUSE while it runs] Done. Ten seconds. Rohan at
the top with eighty, invited. Aoife right behind at seventy-seven, also
invited. Both have directly relevant analyst experience. Emma the business
graduate is at fifty-seven, on hold. Priya the senior engineer is at
fifty-one, also on hold. That one is the interesting result, because her CV
is technically the strongest. But the role is junior, and the rubric weighs
role fit, not absolute experience. So the system correctly flags her as
overqualified rather than inviting her. At the bottom, Sean and Liam, both
rejected."

[Click into Rohan Mehta on the dashboard, if live]

---

## Slide 8 - Detail View (5:00 to 5:45)

"When I click into a candidate, this is what the recruiter sees. The
seven-criterion score breakdown with evidence pulled from the CV. The
strengths, the gaps, the LLM rationale. On the right, the draft email,
which is editable. And underneath, three buttons. Approve and send.
Override to reject. Or hold for later. Every action logged. The candidate-
facing email is never sent without a recruiter clicking approve. That
click is the accountability point."

[Advance to slide 9]

---

## Slide 9 - Results (5:45 to 6:15)

"The headline result. Per-applicant recruiter attention drops from about
twelve minutes to roughly thirty seconds. That is a twenty-four times
improvement. Every CV is now scored on the same rubric. Every decision is
logged with its rationale. And crucially, the ranking the system produces
matches the ordering I would come up with if I read all six CVs manually.
That is the validation I wanted."

[Advance to slide 10]

---

## Slide 10 - Ethics (6:15 to 6:40)

"Quickly on ethics because it matters. Human-in-the-loop is not optional.
Every email needs a recruiter click. Scoring is evidence-linked, which
means every score is defensible under GDPR Article fifteen if a candidate
asks. Bias mitigation through the structured rubric. And the EU AI Act
classifies recruitment as high-risk, so the audit trail and human oversight
are legal requirements, not extras."

[Advance to slide 11]

---

## Slide 11 - Conclusion (6:40 to 7:00)

"To wrap up. Both BPMN models done. Automation analysis done. RPA layer,
agentic layer, dashboard, and a working demo, done. If I were to extend it
I would add RAG over past hires, periodic rubric recalibration, ATS
integration, and formal bias measurement. Thank you for watching. Happy to
take questions."

[End on slide 11. Hold for 2 seconds. Stop recording.]

---

## Recording checklist

Before you hit record:
- [ ] Wired headset mic connected. Test it. Cheap wired earbuds beat laptop mic.
- [ ] Quiet room. Windows shut. Notifications off. Phone on silent.
- [ ] Slide deck open in Presenter mode. Speaker notes on second monitor.
- [ ] Dashboard already running on localhost:8501. Pipeline results cleared.
- [ ] Timer visible somewhere so you can pace.
- [ ] Water beside you. Room-temperature. Not cold.

During recording:
- [ ] Speak clearly. Slightly slower than you think you should.
- [ ] Pause a beat after each big claim.
- [ ] If you fluff a sentence: pause, breathe, restart that sentence. Cut in post.
- [ ] Use the cursor as a pointer when discussing diagram elements.
- [ ] For slides 7 and 8: switch to the live dashboard and click through it.
- [ ] Keep your energy up throughout. The last two slides matter as much as the first.

After recording:
- [ ] Save as H9IAPA_CA_Video_x24311073.mp4
- [ ] Watch it back once at 1.25x. If anything makes you cringe, re-record just that clip.
- [ ] Check the total length is under 7 minutes.

## Two versions of the intro if you need them

**Standard (25 sec):** the one above.

**Short (15 sec, if you overrun elsewhere):**
"Hi, I'm Esvanth. For H9IAPA I automated recruitment screening using an RPA
layer for the admin work and an agentic AI layer running Llama three point
three for the screening. Let me show you how it works."
