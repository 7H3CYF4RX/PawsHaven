/**
 * Vulnerable SSR Render Endpoint
 * CVE-2025-55182 (React2Shell) — Server-side code execution via template injection
 * 
 * User input flows into server-side eval during template rendering.
 * Payload: /api/render?template=${require('child_process').execSync('id').toString()}
 */

export default function handler(req, res) {
    const { template } = req.query;

    if (!template) {
        return res.status(400).json({
            error: 'Template parameter is required.',
            usage: '/api/render?template=Hello World',
            version: 'PawsHaven Gallery API v1.0 (Next.js 14.1.0)'
        });
    }

    try {
        // VULNERABILITY: User input flows directly into eval()
        // This simulates the React2Shell CVE where SSR template rendering
        // allows server-side JavaScript execution
        const rendered = eval('`' + template + '`');

        return res.status(200).json({
            rendered: rendered,
            engine: 'Next.js SSR Template Engine',
            version: '14.1.0',
            timestamp: new Date().toISOString()
        });
    } catch (e) {
        return res.status(500).json({
            error: 'Template rendering failed',
            details: e.message,
            stack: e.stack
        });
    }
}
