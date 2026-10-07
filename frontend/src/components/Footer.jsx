import { Link } from 'react-router-dom'
import { Brand } from './TopBar.jsx'

export default function Footer() {
  return (
    <footer className="footer no-print">
      <div className="container">
        <div className="footer-inner">
          <div>
            <Brand />
            <p>An AI agent that researches how companies interview and turns it into your personal, practice-ready prep kit.</p>
          </div>
          <div>
            <h4>Product</h4>
            <div className="footer-links">
              <Link to="/new">New prep kit</Link>
              <Link to="/preps">My prep kits</Link>
              <Link to="/new?sample=1">Try a sample</Link>
            </div>
          </div>
          <div>
            <h4>Learn</h4>
            <div className="footer-links">
              <a href="/#how">How it works</a>
              <a href="/#dashboards">The five dashboards</a>
              <a href="/#faq">FAQ</a>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <span>© {new Date().getFullYear()} InstantInterviewPrep</span>
          <span>Built with React, FastAPI and Claude</span>
        </div>
      </div>
    </footer>
  )
}
