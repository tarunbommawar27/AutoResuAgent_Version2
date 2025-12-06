import { useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [jobText, setJobText] = useState('')
  const [resumeText, setResumeText] = useState('')
  const [loading, setLoading] = useState(false)
  const [parsingJob, setParsingJob] = useState(false)
  const [parsingResume, setParsingResume] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('bullets')

  const handleParseJob = async () => {
    if (!jobText.trim()) {
      alert('Please paste job posting text first')
      return
    }

    setParsingJob(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/parse/job`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: jobText })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to parse job')
      }

      const data = await response.json()
      setJobText(data.yaml_content)
    } catch (err) {
      setError(`Job parsing failed: ${err.message}`)
    } finally {
      setParsingJob(false)
    }
  }

  const handleParseResume = async () => {
    if (!resumeText.trim()) {
      alert('Please paste resume text first')
      return
    }

    setParsingResume(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/parse/resume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: resumeText })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to parse resume')
      }

      const data = await response.json()
      const formatted = JSON.stringify(JSON.parse(data.json_content), null, 2)
      setResumeText(formatted)
    } catch (err) {
      setError(`Resume parsing failed: ${err.message}`)
    } finally {
      setParsingResume(false)
    }
  }

  const handleGenerate = async () => {
    if (!jobText.trim() || !resumeText.trim()) {
      alert('Please provide both job posting and resume data')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`${API_BASE_URL}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_yaml: jobText,
          resume_json: resumeText
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Generation failed')
      }

      const data = await response.json()

      if (!data.success) {
        throw new Error(data.errors?.join(', ') || 'Generation failed')
      }

      setResult(data)
      setActiveTab('bullets')
    } catch (err) {
      setError(`Generation failed: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    if (!result) return

    let content = '=== TAILORED COVER LETTER ===\n\n'
    content += result.cover_letter + '\n\n'
    content += '=== TAILORED RESUME BULLETS ===\n\n'

    result.bullets.forEach((bullet, idx) => {
      content += `${idx + 1}. ${bullet.text}\n`
      content += `   [Source: ${bullet.source_experience_id || bullet.source_project_id || 'N/A'}]\n\n`
    })

    if (result.change_summary) {
      content += '\n=== CHANGE SUMMARY ===\n\n'
      content += result.change_summary + '\n\n'
    }

    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `tailored_resume_${result.job_id}_${new Date().toISOString().split('T')[0]}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleCopyLatex = (latexCode, type) => {
    if (!latexCode) {
      alert(`${type} LaTeX code not available`)
      return
    }

    navigator.clipboard.writeText(latexCode).then(() => {
      alert(`${type} LaTeX copied to clipboard!`)
    }).catch(err => {
      alert(`Failed to copy: ${err.message}`)
    })
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Modern Navbar */}
      <nav className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-teal-700 rounded-lg flex items-center justify-center shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">AutoResuAgent</h1>
                <p className="text-xs text-slate-500">AI-Powered Resume Tailoring</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 bg-teal-50 text-teal-700 text-xs font-medium rounded-full border border-teal-200">
                v1.0
              </span>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3 shadow-sm">
            <div className="flex-shrink-0 w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-red-900 text-sm">Error</h3>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Workspace: Split Panel Editor */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Job Editor Panel */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="bg-slate-100 border-b border-slate-200 px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-teal-500"></div>
                <span className="text-sm font-semibold text-slate-700">Job Posting</span>
              </div>
              <div className="flex items-center gap-2">
                {parsingJob ? (
                  <span className="px-3 py-1 bg-amber-50 text-amber-700 text-xs font-medium rounded-full border border-amber-200 flex items-center gap-2 pulse-slow">
                    <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Parsing...
                  </span>
                ) : jobText.trim() ? (
                  <span className="px-3 py-1 bg-teal-50 text-teal-700 text-xs font-medium rounded-full border border-teal-200">
                    Ready
                  </span>
                ) : (
                  <span className="px-3 py-1 bg-slate-100 text-slate-500 text-xs font-medium rounded-full border border-slate-200">
                    Empty
                  </span>
                )}
                <button
                  onClick={handleParseJob}
                  disabled={parsingJob || !jobText.trim()}
                  className="px-3 py-1.5 bg-teal-600 text-white text-xs font-medium rounded-lg hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-smooth shadow-sm hover:shadow flex items-center gap-2"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Auto-Parse
                </button>
              </div>
            </div>
            <textarea
              value={jobText}
              onChange={(e) => setJobText(e.target.value)}
              placeholder="Paste raw job posting from LinkedIn, Indeed, or company website...

Click 'Auto-Parse' to convert to structured YAML"
              className="w-full h-96 p-4 bg-slate-50 text-slate-900 font-mono text-xs resize-none focus:outline-none focus:ring-2 focus:ring-inset focus:ring-teal-500 custom-scrollbar"
            />
            <div className="bg-slate-100 border-t border-slate-200 px-4 py-2">
              <p className="text-xs text-slate-600">
                <span className="font-medium">Tip:</span> Paste raw text or provide YAML directly
              </p>
            </div>
          </div>

          {/* Resume Editor Panel */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="bg-slate-100 border-b border-slate-200 px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-teal-500"></div>
                <span className="text-sm font-semibold text-slate-700">Resume / Profile</span>
              </div>
              <div className="flex items-center gap-2">
                {parsingResume ? (
                  <span className="px-3 py-1 bg-amber-50 text-amber-700 text-xs font-medium rounded-full border border-amber-200 flex items-center gap-2 pulse-slow">
                    <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Parsing...
                  </span>
                ) : resumeText.trim() ? (
                  <span className="px-3 py-1 bg-teal-50 text-teal-700 text-xs font-medium rounded-full border border-teal-200">
                    Ready
                  </span>
                ) : (
                  <span className="px-3 py-1 bg-slate-100 text-slate-500 text-xs font-medium rounded-full border border-slate-200">
                    Empty
                  </span>
                )}
                <button
                  onClick={handleParseResume}
                  disabled={parsingResume || !resumeText.trim()}
                  className="px-3 py-1.5 bg-teal-600 text-white text-xs font-medium rounded-lg hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-smooth shadow-sm hover:shadow flex items-center gap-2"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Auto-Parse
                </button>
              </div>
            </div>
            <textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              placeholder="Paste your resume from LinkedIn, PDF export, or text document...

Click 'Auto-Parse' to convert to structured JSON"
              className="w-full h-96 p-4 bg-slate-50 text-slate-900 font-mono text-xs resize-none focus:outline-none focus:ring-2 focus:ring-inset focus:ring-teal-500 custom-scrollbar"
            />
            <div className="bg-slate-100 border-t border-slate-200 px-4 py-2">
              <p className="text-xs text-slate-600">
                <span className="font-medium">Tip:</span> Paste raw text or provide JSON directly
              </p>
            </div>
          </div>
        </div>

        {/* Generate Action Center */}
        <div className="flex justify-center mb-8">
          <button
            onClick={handleGenerate}
            disabled={loading || !jobText.trim() || !resumeText.trim()}
            className="group px-8 py-4 bg-teal-600 text-white text-base font-semibold rounded-xl hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-smooth shadow-lg hover:shadow-glow flex items-center gap-3"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>Generating Tailored Resume...</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>Generate Tailored Resume</span>
              </>
            )}
          </button>
        </div>

        {/* Success Card - Results */}
        {result && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-lg overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-teal-50 to-emerald-50 border-b border-teal-100 px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-teal-600 rounded-lg flex items-center justify-center shadow-sm">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-slate-900">Generation Successful</h2>
                    <p className="text-sm text-slate-600">Your tailored resume is ready</p>
                  </div>
                </div>
                <button
                  onClick={handleDownload}
                  className="px-4 py-2 bg-teal-600 text-white text-sm font-medium rounded-lg hover:bg-teal-700 transition-smooth shadow-sm hover:shadow flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Download
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              {/* Validation Warnings */}
              {result.errors && result.errors.length > 0 && (
                <div className="mb-6 bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <h3 className="font-semibold text-amber-900 text-sm mb-2">Validation Warnings</h3>
                  <ul className="list-disc list-inside text-sm text-amber-800 space-y-1">
                    {result.errors.map((err, idx) => (
                      <li key={idx}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Change Summary */}
              {result.change_summary && (
                <div className="mb-6 bg-teal-50 border border-teal-200 rounded-lg p-5">
                  <h3 className="text-base font-semibold text-slate-900 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    Change Summary
                  </h3>
                  <div className="bg-white rounded-lg p-4 border border-teal-100">
                    <pre className="text-sm text-slate-700 whitespace-pre-line font-sans leading-relaxed">
                      {result.change_summary}
                    </pre>
                  </div>
                </div>
              )}

              {/* Cover Letter */}
              <div className="mb-6">
                <h3 className="text-base font-semibold text-slate-900 mb-3 flex items-center gap-2">
                  <svg className="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  Cover Letter
                </h3>
                <div className="bg-slate-50 rounded-lg p-5 border border-slate-200">
                  <p className="text-sm text-slate-700 whitespace-pre-line leading-relaxed">
                    {result.cover_letter}
                  </p>
                </div>
              </div>

              {/* Tab Navigation */}
              <div className="border-b border-slate-200 mb-4">
                <div className="flex gap-1">
                  <button
                    onClick={() => setActiveTab('bullets')}
                    className={`px-4 py-2.5 text-sm font-medium transition-smooth border-b-2 ${
                      activeTab === 'bullets'
                        ? 'text-teal-700 border-teal-600'
                        : 'text-slate-600 border-transparent hover:text-slate-900 hover:border-slate-300'
                    }`}
                  >
                    Resume Bullets ({result.bullets.length})
                  </button>
                  <button
                    onClick={() => setActiveTab('resume_latex')}
                    className={`px-4 py-2.5 text-sm font-medium transition-smooth border-b-2 ${
                      activeTab === 'resume_latex'
                        ? 'text-teal-700 border-teal-600'
                        : 'text-slate-600 border-transparent hover:text-slate-900 hover:border-slate-300'
                    }`}
                  >
                    Resume LaTeX
                  </button>
                  <button
                    onClick={() => setActiveTab('cover_latex')}
                    className={`px-4 py-2.5 text-sm font-medium transition-smooth border-b-2 ${
                      activeTab === 'cover_latex'
                        ? 'text-teal-700 border-teal-600'
                        : 'text-slate-600 border-transparent hover:text-slate-900 hover:border-slate-300'
                    }`}
                  >
                    Cover Letter LaTeX
                  </button>
                </div>
              </div>

              {/* Tab Content */}
              {activeTab === 'bullets' && (
                <div className="space-y-3">
                  {result.bullets.map((bullet, idx) => (
                    <div
                      key={bullet.id}
                      className="bg-slate-50 rounded-lg p-4 border border-slate-200 hover:border-teal-300 hover:bg-teal-50 transition-smooth"
                    >
                      <div className="flex items-start gap-3">
                        <span className="flex-shrink-0 w-7 h-7 bg-teal-600 text-white rounded-lg flex items-center justify-center font-semibold text-xs shadow-sm">
                          {idx + 1}
                        </span>
                        <div className="flex-1">
                          <p className="text-sm text-slate-900 leading-relaxed">{bullet.text}</p>
                          <div className="mt-2 flex gap-3 text-xs text-slate-500">
                            <span>
                              <strong className="text-slate-700">Responsibility:</strong> {bullet.responsibility_id || 'N/A'}
                            </span>
                            <span>
                              <strong className="text-slate-700">Source:</strong> {bullet.source_experience_id || bullet.source_project_id || 'N/A'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'resume_latex' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-slate-700">Resume LaTeX Source Code</h3>
                    <button
                      onClick={() => handleCopyLatex(result.resume_latex, 'Resume')}
                      disabled={!result.resume_latex}
                      className="px-3 py-1.5 bg-teal-600 text-white text-xs font-medium rounded-lg hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-smooth shadow-sm flex items-center gap-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      Copy
                    </button>
                  </div>
                  {result.resume_latex ? (
                    <div className="code-editor custom-scrollbar max-h-96 overflow-auto">
                      <pre className="text-xs whitespace-pre-wrap break-words">
                        {result.resume_latex}
                      </pre>
                    </div>
                  ) : (
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-amber-800 text-sm">
                      LaTeX code not available. Check server logs for generation errors.
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'cover_latex' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-slate-700">Cover Letter LaTeX Source Code</h3>
                    <button
                      onClick={() => handleCopyLatex(result.cover_letter_latex, 'Cover Letter')}
                      disabled={!result.cover_letter_latex}
                      className="px-3 py-1.5 bg-teal-600 text-white text-xs font-medium rounded-lg hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-smooth shadow-sm flex items-center gap-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      Copy
                    </button>
                  </div>
                  {result.cover_letter_latex ? (
                    <div className="code-editor custom-scrollbar max-h-96 overflow-auto">
                      <pre className="text-xs whitespace-pre-wrap break-words">
                        {result.cover_letter_latex}
                      </pre>
                    </div>
                  ) : (
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-amber-800 text-sm">
                      LaTeX code not available. Check server logs for generation errors.
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Quick Start Guide */}
        {!result && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Quick Start Guide
            </h3>
            <ol className="space-y-2 text-sm text-slate-700">
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-teal-100 text-teal-700 rounded-full flex items-center justify-center font-semibold text-xs">1</span>
                <span>Paste raw job posting in the left panel</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-teal-100 text-teal-700 rounded-full flex items-center justify-center font-semibold text-xs">2</span>
                <span>Click "Auto-Parse" to convert to structured YAML</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-teal-100 text-teal-700 rounded-full flex items-center justify-center font-semibold text-xs">3</span>
                <span>Paste your resume in the right panel</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-teal-100 text-teal-700 rounded-full flex items-center justify-center font-semibold text-xs">4</span>
                <span>Click "Auto-Parse" to convert to structured JSON</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-teal-100 text-teal-700 rounded-full flex items-center justify-center font-semibold text-xs">5</span>
                <span>Click "Generate Tailored Resume" and get your results!</span>
              </li>
            </ol>
            <div className="mt-4 p-3 bg-teal-50 border border-teal-200 rounded-lg">
              <p className="text-xs text-teal-800">
                <strong>Pro Tip:</strong> Copy the generated LaTeX code to compile with pdflatex or upload to Overleaf for a professional PDF resume!
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="mt-12 border-t border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-slate-500 text-xs">
            AutoResuAgent v1.0 • Powered by GPT-4o-mini, Sentence-BERT, and FAISS
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
