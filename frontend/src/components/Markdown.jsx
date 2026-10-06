import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'

const remarkPlugins = [remarkGfm]
const rehypePlugins = [[rehypeHighlight, { detect: false }]]
const components = {
  a: ({ node, ...props }) => <a {...props} target="_blank" rel="noreferrer noopener" />,
}

// Raw HTML is never rendered (no rehype-raw), so AI- or user-provided text can't inject markup.
export default function Markdown({ children, className = '' }) {
  if (children === null || children === undefined || children === '') return null
  return (
    <div className={`md ${className}`}>
      <ReactMarkdown remarkPlugins={remarkPlugins} rehypePlugins={rehypePlugins} components={components}>
        {String(children)}
      </ReactMarkdown>
    </div>
  )
}

const LANGUAGE_ALIASES = { py: 'python', js: 'javascript', ts: 'typescript', sh: 'bash', text: 'plaintext', txt: 'plaintext' }

/** Wrap a {language, code} snippet in a fenced block that survives backticks in the code. */
export function codeFence(snippet) {
  if (!snippet || !snippet.code) return ''
  const raw = (snippet.language || '').trim().toLowerCase()
  const lang = LANGUAGE_ALIASES[raw] || raw.replace(/[^a-z0-9+#-]/g, '') || 'plaintext'
  const fence = snippet.code.includes('```') ? '````' : '```'
  return `${fence}${lang}\n${snippet.code.replace(/\s+$/, '')}\n${fence}`
}
