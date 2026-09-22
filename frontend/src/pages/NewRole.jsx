// HR form for defining a role and the skills it's measured against.
import { useState } from 'react'
import { api } from '../api'
import { ErrorNote } from '../components/Status.jsx'

const emptySkill = () => ({ name: '', weight: 2, required_level: 3, critical: false })

export default function NewRole() {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [skills, setSkills] = useState([emptySkill(), emptySkill()])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const update = (index, field, value) =>
    setSkills((list) => list.map((s, i) => (i === index ? { ...s, [field]: value } : s)))

  const save = async () => {
    setBusy(true)
    setError('')
    try {
      await api.createRole({
        title,
        description,
        skills: skills
          .filter((s) => s.name.trim())
          .map((s) => ({ ...s, weight: Number(s.weight), required_level: Number(s.required_level) })),
      })
      window.location.hash = '#/'
    } catch (e) {
      setError(e.message)
      setBusy(false)
    }
  }

  const namedSkills = skills.filter((s) => s.name.trim()).length

  return (
    <>
      <p><a href="#/">Back to dashboard</a></p>
      <h1>Add a role</h1>

      <section className="panel">
        <label className="block">
          Role title
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Frontend Developer" />
        </label>
        <label className="block">
          Short description
          <textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)}
            placeholder="What this person will do day to day. The interviewer uses this for context." />
        </label>
      </section>

      <section className="panel">
        <h2>Skills</h2>
        <p className="muted">
          Reuse the exact names of skills from other roles where they overlap, so one interview can be
          compared across roles. The interviewer asks about the critical and most important skills first.
        </p>

        <div className="skill-grid" role="table" aria-label="Skills">
          <div className="skill-grid-head" role="row">
            <span role="columnheader">Skill</span>
            <span role="columnheader">Importance</span>
            <span role="columnheader">Level needed</span>
            <span role="columnheader">Critical</span>
            <span role="columnheader"><span className="visually-hidden">Remove</span></span>
          </div>
          {skills.map((s, i) => (
            <div className="skill-grid-row" role="row" key={i}>
              <input aria-label="Skill name" value={s.name} onChange={(e) => update(i, 'name', e.target.value)}
                placeholder="e.g. React" />
              <select aria-label="Importance" value={s.weight} onChange={(e) => update(i, 'weight', e.target.value)}>
                <option value={1}>Nice to have</option>
                <option value={2}>Important</option>
                <option value={3}>Core</option>
              </select>
              <select aria-label="Level needed" value={s.required_level}
                onChange={(e) => update(i, 'required_level', e.target.value)}>
                <option value={1}>1: Aware</option>
                <option value={2}>2: Basic</option>
                <option value={3}>3: Working</option>
                <option value={4}>4: Strong</option>
                <option value={5}>5: Expert</option>
              </select>
              <input type="checkbox" aria-label="Critical" checked={s.critical}
                onChange={(e) => update(i, 'critical', e.target.checked)} />
              <button className="quiet" onClick={() => setSkills((l) => l.filter((_, j) => j !== i))}
                disabled={skills.length === 1}>Remove</button>
            </div>
          ))}
        </div>
        <button onClick={() => setSkills((l) => [...l, emptySkill()])} disabled={skills.length >= 12}>
          Add skill
        </button>
      </section>

      <ErrorNote>{error}</ErrorNote>
      <div className="actions-bar">
        <button className="primary" onClick={save} disabled={busy || title.trim().length < 2 || namedSkills === 0}>
          {busy ? 'Saving…' : 'Save role'}
        </button>
        <a href="#/">Cancel</a>
      </div>
    </>
  )
}
