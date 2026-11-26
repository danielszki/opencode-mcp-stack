---
name: expert
description: >
  Turn a task or prompt into a deeper version of itself, not a bigger one.
  Before rewriting, say what a top professional in the field would do that the
  user isn't asking for, the rawest source material they would start from, the
  specific methods and tools they would use, what (other than the user or the
  model) would show the result is right, how the work most likely fails, what
  must stay untouched, what is still unverified, and the first step. Then
  rewrite the prompt to ask for exactly that. USE WHEN: /expert, "be
  ambitious", "make this prompt deeper", "what would an expert do here", "raise
  the bar on this task", "rewrite my prompt like a pro would ask it". NOT FOR:
  expanding scope, adding features, or general prompt polishing for tone or
  length.
---

# Expert

Grew out of a prompt shared by Felix Rieseberg (Anthropic) and the
`be-ambitious` skill by DannyMac180 that packaged it:

> I want a deeper version of this task, not a bigger one. Before rewriting it:
> (1) say what a top professional in this field would do here that I'm not
> asking for; (2) name the rawest material they would start from instead of
> what has already been digested for me; (3) name the specific methods and
> tools they would use; (4) say what, other than you or me, would show the
> result is right. Then rewrite my prompt to ask for exactly that.

## Input

The task is the whole message that contains `/expert`, wherever the tag sits
(people often type it at the end, after the task), together with anything
attached to it: images, files, pasted text. If the message holds nothing but
the tag, use the user's most recent request in this conversation. If there is
none, ask for the task in one line and stop. Calling the skill is the request
for a rewrite, not for the work: do not start editing or running the task.

## Deeper, not bigger

Keep the user's goal and scope. Depth means a higher standard for the same
outcome: better sources, sharper methods, real verification. Do not add
deliverables, features, or side quests. If a suggestion would make the job
larger rather than better, drop it.

## Answer for this task, not for any task

The rewritten prompt is read by a session that acts on it and does not
re-check it, so a guess written as a fact becomes a false premise there. Three
habits keep the answers honest:

- **Specific.** Name the actual thing, not the category. A line that would read
  the same for any task is not answered yet.
- **Provenance.** Every technical claim (a behavior of the code, a fact about a
  system, a tip on how to do it) is marked `(checked: <command or file>)` or
  `(not checked: <where it came from>)`. Run the command before writing
  `checked`; a tip remembered but not run is `not checked`. A fact the user
  stated and nobody verified is `(not checked: said by the user)`. When you
  could check nothing at all (no access to the code, the files or the
  sources), say so once under "Not checked" and mark only the user's unverified
  statements of fact; the same mark on every line hides the ones that matter.
  A decision the user made ("no discount") is settled, not a fact to verify:
  it never takes a mark. A well-known framework named from memory needs no
  mark either; a specific claim about it (a number, a version, a quote) does.
- **Honest gaps.** Write `none`, with the reason, when a line does not apply,
  and `I don't know` rather than naming a source or tool you are not sure
  exists.

## Steps

Name the **field** first: the profession whose standard applies (e.g.
"investigative journalism", "SRE incident response", "clinical pharmacology",
"essay editing"). Then answer these lines for that field. They appear once in
the reply, inside the rewritten prompt; do not print them a second time before
it:

1. **Done when.** One sentence that a third party could check.
2. **Expert moves.** The two or three things that separate expert work from
   competent work here and that the user did not ask for, such as stating the
   decision the work serves, reproducing before fixing, or writing the
   counter-argument. Take the outside view before the inside one (Kahneman and
   Lovallo's reference-class idea): name the class of similar jobs and what
   usually happens in it (how long it takes, how often it meets its goal;
   failure causes belong in line 6, not here), so
   the plan starts from that base rate and adjusts for what is really
   different here. If you don't know the base rate, say so; don't invent one.
3. **Raw material.** The primary sources to start from instead of summaries:
   the dataset, not the chart; the filing, not the article; the logs and the
   code, not the bug report; the paper's methods section, not the abstract. Say
   where it lives if you know.
4. **Methods.** This line is the heart of the rewrite: the working frameworks
   that the best people in this field actually use for this kind of job. Name
   each one by its proper name (the way a physician names differential
   diagnosis, a lawyer IRAC, a reporter the inverted pyramid: these show the
   form only, take yours from this task's own field), say who it comes from or where it is documented, and
   say why it fits this task better than the obvious approach. Pick the one or
   two that fit and make their steps the structure of the work, so the rewritten
   prompt walks through the framework instead of mentioning it. Then the named
   techniques, instruments, libraries or commands that serve it. A generic
   label ("best practices", "a structured approach") is not an answer.
5. **External check.** What, other than the user or the model, would show the
   result is right: a test suite or benchmark, a reproduction, ground-truth
   data, a known answer, a measurement, a domain expert or reviewer, a real
   user's behavior. Say what counts as a pass and what counts as a failure.
6. **Likely failure.** Run a premortem (Gary Klein): assume the work is done
   and has already failed, then write the most plausible cause. Asking "why did
   it fail?" surfaces concrete causes that "what could go wrong?" leaves out.
   Name that cause for this task, not a generic risk, and the early signal on
   which to stop and re-plan.
7. **Off the table.** What must stay untouched even if it looks helpful, each
   with its reason. A limit with its reason gets applied correctly to cases it
   did not foresee.
8. **Not checked.** What you did not verify, and the one observation that would
   overturn the task's premise.
9. **First step.** One concrete action. If a single prerequisite would make the
   whole task worthless when false, verifying it is the first step.

Before rewriting, read the answers against what the user already decided in
this conversation (what they chose, what they rejected): every move and limit
agrees with those decisions. Quote a decision in the user's own words and
language; translating it changes it.

## Rewrite

Then write the rewritten prompt in a single fenced block the user can copy:
one paragraph stating the task in the user's terms, then the field and the
nine lines, each labeled as above. It asks for exactly what the answers
describe: start from the raw material, use the named methods, respect the
limits, begin the work with the first step and judge it by the external check
and its pass criterion. Keep the provenance marks in it. Write it in the user's voice
(first person: "I don't want…", never the user's name or "the user said") and
as long as it needs to be.

After the block, in two to four bullets, say what was raised: what the
rewrite contains that the user did not ask for, and what in it is still
unverified.

Stop there. Offer in one line to run it now; don't start the task unless the
user says so.
