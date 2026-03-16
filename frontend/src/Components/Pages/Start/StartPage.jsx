import React, { useEffect, useRef, useCallback, useState } from 'react'
import { createPortal } from 'react-dom'
import './StartPage.css'
import { Link } from 'react-router-dom'
import { SiCanvas, SiTodoist } from 'react-icons/si'
import { RxNotionLogo } from 'react-icons/rx'
import { IoClose } from 'react-icons/io5'
import scIcon from '../../assets/iconSC.png'

/* ── Scroll-reveal hook ──────────────────────────── */
const useScrollReveal = () => {
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add('in-view')
          observer.unobserve(el)
        }
      },
      { threshold: 0.15 }
    )

    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  return ref
}

import ParticleBackground from '../../Shared/ParticleBackground'

/* ── Mouse-tracking glow on cards ────────────────── */

/* ── Mouse-tracking glow on cards ────────────────── */
const useCardGlow = () => {
  const ref = useRef(null)

  const handleMove = useCallback((e) => {
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    el.style.setProperty('--glow-x', `${e.clientX - rect.left}px`)
    el.style.setProperty('--glow-y', `${e.clientY - rect.top}px`)
  }, [])

  const handleLeave = useCallback(() => {
    const el = ref.current
    if (!el) return
    el.style.removeProperty('--glow-x')
    el.style.removeProperty('--glow-y')
  }, [])

  return { ref, handleMove, handleLeave }
}

/* ── Composable card wrapper ─────────────────────── */
const GlowCard = ({ children, className = '', revealRef }) => {
  const glow = useCardGlow()

  // Merge the two refs
  const mergedRef = useCallback((node) => {
    glow.ref.current = node
    if (typeof revealRef === 'function') revealRef(node)
    else if (revealRef) revealRef.current = node
  }, [revealRef, glow.ref])

  return (
    <div
      className={`start-card glow-card ${className}`}
      ref={mergedRef}
      onMouseMove={glow.handleMove}
      onMouseLeave={glow.handleLeave}
    >
      {children}
    </div>
  )
}

/* ── Video Popup Modal ───────────────────────────── */
const VideoPopup = ({ isOpen, onClose }) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'auto'
    }
    return () => { document.body.style.overflow = 'auto' }
  }, [isOpen])

  if (!isOpen) return null

  return createPortal(
    <div className="video-popup-overlay" onClick={onClose}>
      <div className="video-popup-content" onClick={e => e.stopPropagation()}>
        <button className="video-popup-close" onClick={onClose}>
          <IoClose />
        </button>
        <div className="video-wrapper">
          <video
            src="/demo.mp4"
            controls
            autoPlay
            className="popup-video-player"
            onError={(e) => console.error("Video failed to load", e)}
          >
            Your browser does not support the video tag.
          </video>
          {/* Fallback text if video is missing (styled in CSS) */}
          <div className="video-placeholder-text">
            Video not found: /demo.mp4
          </div>
        </div>
      </div>
    </div>,
    document.body
  )
}

/* ══════════════════════════════════════════════════ */

const StartPage = () => {
  console.log('StartPage mounted - checking for animations')
  const [isDemoOpen, setIsDemoOpen] = useState(false)
  const heroRef = useScrollReveal()
  const aboutRef = useScrollReveal()
  const flowRef = useScrollReveal()
  const stepsRef = useScrollReveal()
  const ctaRef = useScrollReveal()

  return (
    <div className="start-container">

      {/* Ambient particles background */}
      <ParticleBackground />

      {/* Video Popup */}
      <VideoPopup isOpen={isDemoOpen} onClose={() => setIsDemoOpen(false)} />

      {/* ── Hero ──────────────────────────────────── */}
      <section className="start-hero reveal" ref={heroRef}>
        <h1 className="start-hero-title">Student Connect</h1>
        <p className="start-tagline">
          Automate your academic workflow — effortlessly.
        </p>
        <div className="start-hero-buttons">
          <Link to="/register" className="start-cta">Get Started</Link>
          <button
            className="start-cta-outline"
            onClick={() => setIsDemoOpen(true)}
          >
            Watch Demo
          </button>
        </div>
      </section>

      {/* ── What is Student Connect? ──────────────── */}
      <GlowCard className="reveal reveal-up" revealRef={aboutRef}>
        <h2>What is Student Connect?</h2>
        <p>
          Student Connect bridges the gap between your Learning Management System
          and the productivity tools you already use. It automatically pulls your
          upcoming assignments from <strong>Canvas LMS</strong> and syncs them
          straight into <strong>Todoist</strong> or <strong>Notion</strong> —
          so you never miss a deadline and never have to copy things over manually.
        </p>
      </GlowCard>

      {/* ── Integration Flow ─────────────────────── */}
      <GlowCard className="reveal reveal-up" revealRef={flowRef}>
        <h2>Seamless Integrations</h2>
        <div className="start-integrations">
          <div className="start-integration-item stagger-item" style={{ '--i': 0 }}>
            <div className="start-icon-circle pulse-icon"><SiCanvas /></div>
            <span>Canvas</span>
          </div>

          <span className="start-flow-arrow stagger-item" style={{ '--i': 1 }}>
            <svg width="36" height="16" viewBox="0 0 36 16"><path d="M0 8h30m0 0l-6-5m6 5l-6 5" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" fill="none" /></svg>
          </span>

          <div className="start-integration-item stagger-item" style={{ '--i': 2 }}>
            <div className="start-icon-circle pulse-icon" style={{ fontSize: '22px' }}>
              <img src={scIcon} alt="Student Connect" style={{ width: 32, height: 32, borderRadius: '6px' }} />
            </div>
            <span>Student Connect</span>
          </div>

          <span className="start-flow-arrow stagger-item" style={{ '--i': 3 }}>
            <svg width="36" height="16" viewBox="0 0 36 16"><path d="M0 8h30m0 0l-6-5m6 5l-6 5" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" fill="none" /></svg>
          </span>

          <div className="start-integration-item stagger-item" style={{ '--i': 4 }}>
            <div className="start-icon-circle pulse-icon"><SiTodoist /></div>
            <span>Todoist</span>
          </div>

          <span className="start-divider-text stagger-item" style={{ '--i': 5 }}>/</span>

          <div className="start-integration-item stagger-item" style={{ '--i': 6 }}>
            <div className="start-icon-circle pulse-icon"><RxNotionLogo /></div>
            <span>Notion</span>
          </div>
        </div>
      </GlowCard>

      {/* ── How It Works ─────────────────────────── */}
      <GlowCard className="reveal reveal-up" revealRef={stepsRef}>
        <h2>How It Works</h2>
        <ol className="start-steps">
          <li className="start-step stagger-item" style={{ '--i': 0 }}>
            <div className="start-step-number">1</div>
            <span className="start-step-text">
              Link your Canvas account and connect Todoist or Notion.
            </span>
          </li>
          <li className="start-step stagger-item" style={{ '--i': 1 }}>
            <div className="start-step-number">2</div>
            <span className="start-step-text">
              Click <strong>Sync</strong> from the dashboard to pull your assignments.
            </span>
          </li>
          <li className="start-step stagger-item" style={{ '--i': 2 }}>
            <div className="start-step-number">3</div>
            <span className="start-step-text">
              Your tasks appear automatically — organized and ready to go.
            </span>
          </li>
        </ol>
      </GlowCard>

      {/* ── Bottom CTA ───────────────────────────── */}
      <div className="start-bottom-cta reveal reveal-up" ref={ctaRef}>
        <Link to="/register" className="start-cta">Create Your Account</Link>
        <p>Already have an account? <Link to="/login">Login</Link></p>
      </div>

    </div>
  )
}

export default StartPage
