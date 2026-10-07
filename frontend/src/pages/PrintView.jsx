import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, LoaderCircle, Printer } from 'lucide-react'
import { api } from '../api.js'
import Markdown, { codeFence } from '../components/Markdown.jsx'
import { LEVELS, LEVEL_LABEL } from '../components/Badges.jsx'

const KEYS = 'ABCDEF'

function Bullets({ items }) {
  if (!items?.length) return null
  return (
    <ul>
      {items.map((t, i) => (
        <li key={i}>{t}</li>
      ))}
    </ul>
  )
}

function QuestionSection({ title, items, render }) {
  if (!items?.length) return null
  return (
    <section className="print-section">
      <h2>
        {title} ({items.length})
      </h2>
      {LEVELS.map((level) => {
        const group = items.filter((i) => i.level === level)
        if (!group.length) return null
        return (
          <div key={level}>
            <h3>{LEVEL_LABEL[level]}</h3>
            {group.map((item, n) => (
              <div key={item.id} className="card card-flat" style={{ marginBottom: 12 }}>
                <strong>
                  Q{n + 1}. {item.question} {item.hot ? '🔥' : ''}
                </strong>
                <div className="subtle">
                  {item.topic}
                  {item.hot_reason ? ` · ${item.hot_reason}` : ''}
                </div>
                {render(item)}
              </div>
            ))}
          </div>
        )
      })}
    </section>
  )
}

export default function PrintView() {
  const { id } = useParams()
  const [session, setSession] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getSession(id).then(setSession).catch((e) => setError(e.message))
  }, [id])

  if (error) return <main className="page"><div className="banner error">{error}</div></main>
  if (!session) {
    return (
      <div className="center-loader">
        <LoaderCircle size={28} className="spin" />
      </div>
    )
  }
  const r = session.result || {}
  const profile = r.profile || {}
  const company = r.company || {}

  return (
    <main className="page" style={{ maxWidth: 900 }}>
      <div className="row no-print" style={{ marginBottom: 18 }}>
        <Link className="btn" to={`/prep/${id}`}>
          <ArrowLeft size={16} /> Back to dashboards
        </Link>
        <button className="btn btn-primary" onClick={() => window.print()}>
          <Printer size={16} /> Print / save as PDF
        </button>
      </div>

      <h1>
        Interview crash sheet: {session.company} · {session.role || profile.target_role}
      </h1>
      <p className="muted">
        {session.years_experience} years of experience · generated {new Date(session.created_at).toLocaleDateString()}
      </p>

      {profile.elevator_pitch && (
        <section>
          <h2>Tell me about yourself</h2>
          <p className="pitch">{profile.elevator_pitch}</p>
          <div className="two-col">
            <div>
              <h3>Strengths</h3>
              <Bullets items={profile.strengths} />
            </div>
            <div>
              <h3>Gaps to prepare</h3>
              <Bullets items={profile.gaps} />
            </div>
          </div>
        </section>
      )}

      {(company.interview_rounds || []).length > 0 && (
        <section>
          <h2>Interview process</h2>
          <ol>
            {company.interview_rounds.map((rd, i) => (
              <li key={i}>
                <strong>{rd.name}</strong> ({rd.format}) - {rd.what_they_test}
                {rd.tips ? ` Tip: ${rd.tips}` : ''}
              </li>
            ))}
          </ol>
          {(company.reported_questions || []).length > 0 && (
            <>
              <h3>Reported questions</h3>
              <Bullets items={company.reported_questions.map((q) => `${q.question}${q.source ? ` (${q.source})` : ''}`)} />
            </>
          )}
        </section>
      )}

      {(r.revision || []).length > 0 && (
        <section className="print-section">
          <h2>Crash revision</h2>
          {r.revision.map((note) => (
            <div key={note.id} style={{ marginBottom: 22 }}>
              <h3>{note.topic}</h3>
              <p>
                <em>{note.summary}</em>
              </p>
              {(note.key_concepts || []).length > 0 && (
                <ul>
                  {note.key_concepts.map((c, i) => (
                    <li key={i}>
                      <strong>{c.term}:</strong> {c.explanation}
                    </li>
                  ))}
                </ul>
              )}
              <Markdown>{note.explanation_md}</Markdown>
              <Markdown>{codeFence(note.code_example)}</Markdown>
              {(note.cheat_sheet || []).length > 0 && (
                <>
                  <strong>Cheat sheet</strong>
                  <Bullets items={note.cheat_sheet} />
                </>
              )}
            </div>
          ))}
        </section>
      )}

      <QuestionSection
        title="Theoretical questions"
        items={r.theory}
        render={(q) => (
          <>
            <Markdown>{q.answer_md}</Markdown>
            {q.interview_tip && <p><strong>In the interview:</strong> {q.interview_tip}</p>}
          </>
        )}
      />
      <QuestionSection
        title="Practical questions"
        items={r.practical}
        render={(q) => (
          <>
            <Markdown>{q.context}</Markdown>
            <Markdown>{q.solution_md}</Markdown>
            <Markdown>{codeFence(q.code)}</Markdown>
            {q.complexity && <p><strong>Complexity:</strong> {q.complexity}</p>}
          </>
        )}
      />
      <QuestionSection
        title="Scenario-based questions"
        items={r.scenario}
        render={(q) => (
          <>
            <Markdown>{q.scenario}</Markdown>
            <ol>
              {(q.approach_steps || []).map((s, i) => (
                <li key={i}>
                  <strong>{s.step}</strong> - {s.detail}
                </li>
              ))}
            </ol>
            <Markdown>{q.model_answer_md}</Markdown>
          </>
        )}
      />

      {(r.quiz || []).length > 0 && (
        <section className="print-section">
          <h2>MCQ quiz ({r.quiz.length})</h2>
          <ol>
            {r.quiz.map((q) => (
              <li key={q.id} style={{ marginBottom: 10 }}>
                <Markdown>{q.question}</Markdown>
                <div>
                  {q.options.map((o, i) => (
                    <div key={i}>
                      {KEYS[i]}. {o}
                    </div>
                  ))}
                </div>
              </li>
            ))}
          </ol>
          <h3>Answer key</h3>
          <ol>
            {r.quiz.map((q) => (
              <li key={q.id}>
                <strong>{KEYS[q.correct_index]}</strong> - {q.explanation}
              </li>
            ))}
          </ol>
        </section>
      )}
    </main>
  )
}
