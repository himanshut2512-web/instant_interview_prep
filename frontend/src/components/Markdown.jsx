import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { Check, Copy } from 'lucide-react'

const remarkPlugins = [remarkGfm]
const rehypePlugins = [[rehypeHighlight, { detect: false }]]

const EXTENSIONS = {
  python: 'py', sql: 'sql', javascript: 'js', typescript: 'ts', java: 'java', dax: 'dax', bash: 'sh', shell: 'sh',
  markdown: 'md', json: 'json', yaml: 'yml', plaintext: 'txt', text: 'txt', r: 'R', go: 'go', cpp: 'cpp', c: 'c',
  csharp: 'cs', scala: 'scala', kotlin: 'kt', html: 'html', css: 'css', tableau: 'twb',
}
const LABELS = { cpp: 'C++', csharp: 'C#', sql: 'SQL', dax: 'DAX', plaintext: 'Text', json: 'JSON', yaml: 'YAML', r: 'R' }

function hastText(node) {
  if (!node) return ''
  if (node.type === 'text') return node.value
  return (node.children || []).map(hastText).join('')
}

/** Editor-style frame for fenced code: file name, language, line numbers and copy. */
function CodeFrame({ node, children }) {
  const [copied, setCopied] = useState(false)
  const codeNode = (node?.children || []).find((child) => child.tagName === 'code')
  const classes = codeNode?.properties?.className || []
  const languageClass = classes.map(String).find((c) => c.startsWith('language-'))
  const language = languageClass ? languageClass.slice('language-'.length) : ''
  const text = hastText(codeNode).replace(/\n$/, '')
  const lineCount = text ? text.split('\n').length : 1
  const fileName = language === 'dockerfile' ? 'Dockerfile' : `snippet${EXTENSIONS[language] ? `.${EXTENSIONS[language]}` : ''}`

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <figure className="code">
      <div className="code-head">
        <span className="code-dots" aria-hidden="true">
          <i />
          <i />
          <i />
        </span>
        <span className="code-file">{fileName}</span>
        <span className="code-lang">{LABELS[language] || language || 'code'}</span>
        <button type="button" className={`code-copy ${copied ? 'done' : ''}`} onClick={copy} aria-label="Copy code">
          {copied ? <Check size={13} /> : <Copy size={13} />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <div className="code-body">
        <div className="code-gutter" aria-hidden="true">
          {Array.from({ length: lineCount }, (_, i) => i + 1).join('\n')}
        </div>
        <pre>{children}</pre>
      </div>
    </figure>
  )
}

const components = {
  a: ({ node, ...props }) => <a {...props} target="_blank" rel="noreferrer noopener" />,
  pre: CodeFrame,
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
