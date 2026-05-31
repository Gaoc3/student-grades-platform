const fs = require('fs');
const vm = require('vm');

// Read active player URL from command line arguments
const playerUrl = process.argv[2] || "https://web53112x.faselhdx.bid/video_player";
let parsedUrl;
try {
    parsedUrl = new URL(playerUrl);
} catch (e) {
    parsedUrl = new URL("https://web53112x.faselhdx.bid/video_player");
}

// Read all HTML data from stdin
let htmlContent = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
    htmlContent += chunk;
});
process.stdin.on('end', () => {
    try {
        const result = deobfuscatePlayer(htmlContent, playerUrl, parsedUrl);
        console.log(JSON.stringify(result));
    } catch (e) {
        console.log(JSON.stringify({ error: e.message }));
    }
});

function deobfuscatePlayer(html, url, parsed) {
    // Extract script blocks
    const scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
    let match;
    const scripts = [];
    while ((match = scriptRegex.exec(html)) !== null) {
        scripts.push(match[1]);
    }
    
    // Find the large deobfuscator script block (Script 7) containing 'while(!!['
    let deobfScript = '';
    for (let s of scripts) {
        if (s.includes('while(!![') && s.length > 10000) {
            deobfScript = s;
            break;
        }
    }
    
    // Fallback to index 7 if not found by pattern
    if (!deobfScript) {
        deobfScript = scripts[7] || '';
    }
    
    if (!deobfScript) {
        throw new Error("Deobfuscation script block not found");
    }
    
    const capturedButtons = [];
    
    // Mock standard document.write to capture the buttons injected by the deobfuscator
    const mockDocument = {
        write: function(htmlStr) {
            // Pattern: <button class="hd_btn " data-url="URL">QUALITY</button>
            const btnRegex = /<button[^>]*data-url=["']([^"']+)["'][^>]*>([^<]+)<\/button>/gi;
            let m;
            while ((m = btnRegex.exec(htmlStr)) !== null) {
                capturedButtons.push({
                    quality: m[2].trim(),
                    url: m[1].trim()
                });
            }
        },
        createElement: () => ({ style: {} }),
        getElementById: () => ({ style: {} }),
        querySelector: () => ({ setAttribute: () => {}, getAttribute: () => "" }),
        cookie: ""
    };
    
    const mockWindow = {
        location: {
            href: url,
            hostname: parsed.hostname,
            search: parsed.search
        },
        addEventListener: () => {},
        removeEventListener: () => {}
    };
    
    const sandbox = {
        console: { log: () => {}, error: () => {}, warn: () => {} },
        setTimeout: () => {},
        clearTimeout: () => {},
        setInterval: () => {},
        clearInterval: () => {},
        document: mockDocument,
        window: mockWindow,
        $: () => ({ on: () => {} }),
        jQuery: () => ({ on: () => {} }),
        navigator: {
            userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    };
    
    sandbox.window.document = sandbox.document;
    sandbox.document.defaultView = sandbox.window;
    
    // Compile and run script in new context with 1.5s timeout to prevent infinite loops
    const script = new vm.Script(deobfScript, { filename: 'deobf.js' });
    script.runInNewContext(sandbox, { timeout: 1500 });
    
    return { servers: capturedButtons };
}
