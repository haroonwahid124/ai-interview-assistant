// simple hash router, e.g. #/interview/abc
import { useEffect, useState } from 'react'
import Dashboard from './pages/Dashboard.jsx'
import NewRole from './pages/NewRole.jsx'
import InterviewRoom from './pages/InterviewRoom.jsx'
import HrReport from './pages/HrReport.jsx'
import CandidateReport from './pages/CandidateReport.jsx'

const routes = [
  { pattern: /^#\/$/, page: () => <Dashboard />, area: 'hr' },
  { pattern: /^#\/roles\/new$/, page: () => <NewRole />, area: 'hr' },
  { pattern: /^#\/reports\/([\w-]+)$/, page: (id) => <HrReport id={id} />, area: 'hr' },
  { pattern: /^#\/interview\/([\w-]+)$/, page: (id) => <InterviewRoom id={id} />, area: 'candidate' },
  { pattern: /^#\/results\/([\w-]+)$/, page: (id) => <CandidateReport id={id} />, area: 'candidate' },
]

function useHash() {
  const read = () => window.location.hash || '#/'
  const [hash, setHash] = useState(read)
  useEffect(() => {
    const onChange = () => {
      setHash(read())
      window.scrollTo(0, 0)
    }
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])
  return hash
}

export default function App() {
  const hash = useHash()
  const route = routes.find((r) => r.pattern.test(hash))
  const match = route && hash.match(route.pattern)

  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          {route?.area === 'candidate'
            ? <span className="brand">Interview Assistant</span>
            : <a className="brand" href="#/">Interview Assistant</a>}
          {route?.area === 'hr' && <span className="topbar-note">Hiring team</span>}
        </div>
      </header>
      <main className="page">
        {route ? route.page(match[1]) : (
          <section>
            <h1>Page not found</h1>
            <p><a href="#/">Go to the hiring dashboard</a></p>
          </section>
        )}
      </main>
    </>
  )
}
