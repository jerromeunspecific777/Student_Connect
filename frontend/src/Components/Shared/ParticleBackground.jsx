import React, { useEffect, useRef } from 'react'
import './ParticleBackground.css'

const ParticleBackground = () => {
    const canvasRef = useRef(null)

    useEffect(() => {
        const canvas = canvasRef.current
        if (!canvas) return
        const ctx = canvas.getContext('2d')

        let w, h, particles, animId

        const resize = () => {
            w = canvas.width = canvas.offsetWidth
            h = canvas.height = canvas.offsetHeight
        }

        const init = () => {
            resize()
            particles = Array.from({ length: 80 }, () => ({
                x: Math.random() * w,
                y: Math.random() * h,
                r: Math.random() * 3 + 1.2,
                dx: (Math.random() - 0.5) * 0.4,
                dy: (Math.random() - 0.5) * 0.4,
                o: Math.random() * 0.5 + 0.2,
            }))
        }

        const draw = () => {
            ctx.clearRect(0, 0, w, h)
            particles.forEach(p => {
                p.x += p.dx
                p.y += p.dy
                if (p.x < 0 || p.x > w) p.dx *= -1
                if (p.y < 0 || p.y > h) p.dy *= -1
                ctx.beginPath()
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
                ctx.fillStyle = `rgba(255,255,255,${p.o})`
                ctx.fill()
            })

            // Draw faint lines between nearby particles
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x
                    const dy = particles[i].y - particles[j].y
                    const dist = Math.sqrt(dx * dx + dy * dy)
                    if (dist < 120) {
                        ctx.beginPath()
                        ctx.moveTo(particles[i].x, particles[i].y)
                        ctx.lineTo(particles[j].x, particles[j].y)
                        ctx.strokeStyle = `rgba(255,255,255,${0.12 * (1 - dist / 120)})`
                        ctx.lineWidth = 1
                        ctx.stroke()
                    }
                }
            }

            animId = requestAnimationFrame(draw)
        }

        init()
        draw()
        window.addEventListener('resize', resize)
        return () => {
            cancelAnimationFrame(animId)
            window.removeEventListener('resize', resize)
        }
    }, [])

    return <canvas ref={canvasRef} className="particle-background" />
}

export default ParticleBackground
