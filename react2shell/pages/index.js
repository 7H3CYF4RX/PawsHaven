import React from 'react';

export default function Home() {
    return (
        <div style={{ fontFamily: 'Nunito, sans-serif', background: '#faf7f2', minHeight: '100vh', padding: '40px' }}>
            <div style={{ maxWidth: '800px', margin: '0 auto' }}>
                <h1 style={{ color: '#2d6a4f' }}>🐾 PawsHaven Interactive Gallery</h1>
                <p style={{ color: '#5a5a5a' }}>Server-side rendered animal gallery widget.</p>
                <div style={{ marginTop: '20px', background: '#fff', borderRadius: '16px', padding: '24px', border: '1px solid #e8e2d8' }}>
                    <h3>Gallery Renderer</h3>
                    <p>Use the <code>/api/render</code> endpoint to render custom gallery templates.</p>
                    <pre style={{ background: '#1e1e1e', color: '#d4d4d4', padding: '16px', borderRadius: '8px', marginTop: '12px' }}>
{`GET /api/render?template=Hello World
GET /api/render?template=\${7*7}`}
                    </pre>
                </div>
                <p style={{ marginTop: '20px', fontSize: '0.85rem', color: '#8a8a8a' }}>PawsHaven Gallery Widget v1.0 — Powered by Next.js 14.1.0</p>
            </div>
        </div>
    );
}
