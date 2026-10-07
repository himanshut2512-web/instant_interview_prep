import { useRef, useState } from 'react'
import { FileUp, Paperclip, X } from 'lucide-react'

const MAX_MB = 10

export default function FileDrop({ files, onChange, accept = '.pdf,.docx,.txt,.md', multiple = false, label, hint, invalid }) {
  const inputRef = useRef(null)
  const [drag, setDrag] = useState(false)
  const [error, setError] = useState('')
  const allowed = accept.split(',').map((e) => e.trim().toLowerCase())

  const take = (fileList) => {
    const picked = Array.from(fileList || [])
    const bad = picked.find((f) => !allowed.some((ext) => f.name.toLowerCase().endsWith(ext)))
    if (bad) return setError(`"${bad.name}" is not supported. Use ${allowed.join(', ')}.`)
    const big = picked.find((f) => f.size > MAX_MB * 1024 * 1024)
    if (big) return setError(`"${big.name}" is larger than ${MAX_MB} MB.`)
    setError('')
    onChange(multiple ? [...files, ...picked].slice(0, 5) : picked.slice(0, 1))
  }

  return (
    <div className="stack" style={{ gap: 8 }}>
      <div
        className={`dropzone ${drag ? 'drag' : ''} ${invalid ? 'invalid' : ''}`}
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          setDrag(true)
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDrag(false)
          take(e.dataTransfer.files)
        }}
      >
        <span className="dropzone-icon">
          <FileUp size={20} />
        </span>
        <div>
          <strong style={{ fontSize: '0.92rem' }}>{label || 'Drop a file here or click to browse'}</strong>
          <div className="subtle">{hint || `PDF, DOCX, TXT or MD · up to ${MAX_MB} MB`}</div>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          hidden
          onChange={(e) => {
            take(e.target.files)
            e.target.value = ''
          }}
        />
      </div>
      {error && <span className="field-error">{error}</span>}
      {files.length > 0 && (
        <div className="row wrap">
          {files.map((file, i) => (
            <span className="file-pill" key={`${file.name}-${i}`}>
              <Paperclip size={14} />
              <span>{file.name}</span>
              <span className="subtle">{Math.max(1, Math.round(file.size / 1024))} KB</span>
              <button
                type="button"
                className="btn-ghost btn btn-sm"
                style={{ padding: 2 }}
                aria-label={`Remove ${file.name}`}
                onClick={() => onChange(files.filter((_, j) => j !== i))}
              >
                <X size={14} />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
