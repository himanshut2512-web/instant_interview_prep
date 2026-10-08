import { useRef, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { CircleAlert, FileUp, Trash2 } from 'lucide-react'
import { EASE } from '../lib/motion.js'

const MAX_MB = 10
const BADGE = {
  pdf: 'linear-gradient(140deg, #ef4444, #b91c1c)',
  docx: 'linear-gradient(140deg, #3b82f6, #1d4ed8)',
  txt: 'linear-gradient(140deg, #64748b, #334155)',
  md: 'linear-gradient(140deg, #8b5cf6, #6d28d9)',
}

function extension(name) {
  return (name.split('.').pop() || '').toLowerCase()
}

function size(bytes) {
  return bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`
}

export default function FileDrop({ files, onChange, accept = '.pdf,.docx,.txt,.md', multiple = false, label, hint, invalid }) {
  const inputRef = useRef(null)
  const [drag, setDrag] = useState(false)
  const [error, setError] = useState('')
  const allowed = accept.split(',').map((e) => e.trim().toLowerCase())

  const take = (fileList) => {
    const picked = Array.from(fileList || [])
    if (!picked.length) return
    const bad = picked.find((f) => !allowed.some((ext) => f.name.toLowerCase().endsWith(ext)))
    if (bad) return setError(`"${bad.name}" is not supported. Use ${allowed.join(', ')}.`)
    const big = picked.find((f) => f.size > MAX_MB * 1024 * 1024)
    if (big) return setError(`"${big.name}" is larger than ${MAX_MB} MB.`)
    setError('')
    onChange(multiple ? [...files, ...picked].slice(0, 5) : picked.slice(0, 1))
  }

  const showZone = multiple || files.length === 0

  return (
    <div>
      {showZone && (
        <div
          className={`dropzone ${drag ? 'drag' : ''} ${invalid ? 'invalid' : ''}`}
          role="button"
          tabIndex={0}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), inputRef.current?.click())}
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
          <span className="dz-icon">
            <FileUp size={22} />
          </span>
          <span className="dz-text">
            <strong>{label || 'Drop a file here or click to browse'}</strong>
            <span>{hint || `PDF, DOCX, TXT or MD · up to ${MAX_MB} MB`}</span>
          </span>
          <span className="btn btn-sm dz-browse" aria-hidden="true">
            Browse
          </span>
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
      )}
      {error && (
        <div className="field-error" style={{ marginTop: 8 }}>
          <CircleAlert size={14} /> {error}
        </div>
      )}
      <div className="file-list">
        <AnimatePresence initial={false}>
          {files.map((file, i) => {
            const ext = extension(file.name)
            return (
              <motion.div
                key={`${file.name}-${file.size}-${i}`}
                className="file-item"
                layout
                initial={{ opacity: 0, y: 8, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, x: 20, transition: { duration: 0.18 } }}
                transition={{ duration: 0.3, ease: EASE }}
              >
                <span className="file-badge" style={{ background: BADGE[ext] || BADGE.txt }}>
                  {ext.toUpperCase().slice(0, 4)}
                </span>
                <span style={{ minWidth: 0, flex: 1 }}>
                  <span className="name ellipsis" style={{ display: 'block' }}>
                    {file.name}
                  </span>
                  <span className="size">{size(file.size)} · ready to upload</span>
                </span>
                <button type="button" className="icon-btn sm ghost" aria-label={`Remove ${file.name}`} onClick={() => onChange(files.filter((_, j) => j !== i))}>
                  <Trash2 size={16} />
                </button>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </div>
  )
}
