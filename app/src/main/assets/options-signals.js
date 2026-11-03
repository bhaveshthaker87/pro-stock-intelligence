(() => {
'use strict';
const install = () => {
 const nav=document.querySelector('.stock nav.tabs'), stock=document.querySelector('.stock');
 if(!nav||!stock||document.getElementById('psiOptionsWorkspace'))return;
 const tab=document.createElement('button');tab.className='tab';tab.type='button';tab.textContent='Options Signals';tab.id='psiOptionsTab';tab.setAttribute('aria-controls','psiOptionsWorkspace');nav.appendChild(tab);
 const panel=document.createElement('section');panel.id='psiOptionsWorkspace';panel.hidden=true;
 panel.innerHTML = \`
 <div class="psiOptHead"><div><div class="psiOptEyebrow">READ-ONLY OPTIONS INTELLIGENCE</div><h2>Live Options Signals</h2><p>m.Stock + Motilal Oswal · Manual trading decisions only</p></div><span class="psiOptStatus">NOT CONNECTED</span></div>
 <div class="psiOptNotice"><b>Live signals are currently unavailable.</b> Both broker API keys are not generated. This workspace will not invent prices or BUY/SELL calls. It will show signals only after a permitted live feed is authenticated and its timestamps are validated.</div>
 <div class="psiOptGrid">
 <article class="psiOptCard"><div class="psiOptLabel">m.Stock · Mirae Asset</div><strong>API KEY NOT GENERATED</strong><p>WebSocket market-data adapter planned. Static-IP requirement for market-data-only access: broker confirmation pending.</p><a href="https://tradingapi.mstock.com/docs/v1/Introduction/" target="_blank" rel="noopener">Official API documentation ↗</a></article>
 <article class="psiOptCard"><div class="psiOptLabel">Motilal Oswal</div><strong>API KEY NOT GENERATED</strong><p>Market-data WebSocket adapter planned. Static-IP exemption for market-data-only access: broker confirmation pending.</p><a href="https://invest.motilaloswal.com/moAPI/APIDocumentation/Introduction" target="_blank" rel="noopener">Official API documentation ↗</a></article></div>
 <div class="psiOptCard psiOptContract"><div class="psiOptLabel">CONTRACT WATCHLIST · CONFIGURATION ONLY</div><div class="psiOptInputs">
 <label>Underlying<input value="RELIANCE" maxlength="25" autocomplete="off"></label><label>Expiry<input type="date"></label><label>Strike<input type="number" min="0" step="0.05" placeholder="Enter strike"></label><label>Option type<select><option>CALL (CE)</option><option>PUT (PE)</option></select></label></div><p class="psiOptMuted">Selection is configuration only. No broker request is sent and no order can be placed.</p></div>
 <div class="psiOptGrid psiOptMetrics"><article class="psiOptMetric"><span>Underlying LTP</span><b>—</b><small>NO AUTHORIZED LIVE FEED</small></article><article class="psiOptMetric"><span>Option LTP</span><b>—</b><small>NO CONTRACT DATA</small></article><article class="psiOptMetric"><span>Open Interest</span><b>—</b><small>NOT RECEIVED</small></article><article class="psiOptMetric"><span>Last feed timestamp</span><b>—</b><small>NOT CONNECTED</small></article></div>
 <div class="psiOptCard"><div class="psiOptSignalHead"><div><div class="psiOptLabel">SIGNAL ENGINE</div><h3>CALL / PUT decision</h3></div><span class="psiOptBlocked">SIGNALS BLOCKED</span></div><div class="psiOptSignal">NO SIGNAL — broker authentication and live market data are not configured.</div><div class="psiOptSignalGrid"><span>Entry <b>—</b></span><span>Stop-loss <b>—</b></span><span>Target <b>—</b></span><span>Risk / Reward <b>—</b></span></div><p class="psiOptMuted">Planned states: BUY CALL · BUY PUT · HOLD · PARTIAL EXIT · EXIT · RE-ENTRY. A signal requires fresh underlying and option prices, verified contract identity, expiry, and validated inputs. Confidence is not win probability.</p></div>
 <div class="psiOptCard"><div class="psiOptSignalHead"><div><div class="psiOptLabel">PAPER-TRADE AUDIT</div><h3>Signal history & performance</h3></div><span class="psiOptBlocked">0 VERIFIED SIGNALS</span></div><div class="psiOptTableWrap"><table class="psiOptTable"><thead><tr><th>Time</th><th>Contract</th><th>Signal</th><th>Entry</th><th>Exit</th><th>Outcome</th></tr></thead><tbody><tr><td colspan="6">No verified signals yet. History starts only after live-feed validation.</td></tr></tbody></table></div></div>
 <div class="psiOptFooter"><b>Safety:</b> read-only mode · order placement disabled · stale feed blocks signals · no price means no signal · broker secrets must remain server-side, never inside the APK.</div>\`;
 stock.insertAdjacentElement('afterend',panel);
 const style=document.createElement('style');
 style.textContent=\`
 #psiOptionsWorkspace{margin:14px 0 24px;padding:16px;border:1px solid #cbd8e3;border-radius:15px;background:#f6f9fc;color:#102a43;box-shadow:0 8px 22px rgba(16,42,67,.06)}
 #psiOptionsWorkspace[hidden]{display:none!important}.psiOptHead,.psiOptSignalHead{display:flex;justify-content:space-between;align-items:center;gap:12px}
 .psiOptHead h2{font-size:24px;margin:3px 0;color:#102a43}.psiOptHead p{margin:0;color:#536b7e}
 .psiOptEyebrow,.psiOptLabel{font-size:11px;letter-spacing:.7px;font-weight:900;color:#54718a}
 .psiOptStatus,.psiOptBlocked{font-size:11px;font-weight:900;border-radius:999px;padding:7px 11px;background:#fff1d6;color:#9a5b00;border:1px solid #f3d18b}
 .psiOptNotice{margin:13px 0;padding:12px 14px;background:#fff8e9;border:1px solid #f0d69e;border-radius:10px;line-height:1.5}
 .psiOptGrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:12px 0}
 .psiOptCard,.psiOptMetric{background:#fff;border:1px solid #d2dee8;border-radius:12px;padding:14px;min-width:0}
 .psiOptCard strong{display:block;margin:7px 0;color:#183d5c;font-size:15px}.psiOptCard p,.psiOptMuted{color:#5c7184;font-size:12px;line-height:1.5}
 .psiOptCard a{color:#0869d8;font-weight:800;text-decoration:none}.psiOptContract{margin:12px 0}
 .psiOptInputs{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:12px}
 .psiOptInputs label{display:grid;gap:5px;font-size:12px;font-weight:800;color:#3c5870}
 .psiOptInputs input,.psiOptInputs select{width:100%;min-width:0;padding:10px;border:1px solid #bdcedb;border-radius:8px;background:#fff;color:#102a43;font:inherit}
 .psiOptMetrics{grid-template-columns:repeat(4,minmax(0,1fr))}.psiOptMetric span,.psiOptMetric small{display:block;color:#5d758a;font-size:11px}
 .psiOptMetric b{display:block;font-size:22px;margin:7px 0;color:#102a43}.psiOptMetric small{font-size:10px;font-weight:800}
 .psiOptSignalHead h3{margin:4px 0;font-size:17px}.psiOptSignal{margin:12px 0;padding:14px;border-radius:9px;background:#f3f6f9;color:#536b7e;font-weight:900}
 .psiOptSignalGrid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.psiOptSignalGrid span{padding:9px;background:#f7fafc;border:1px solid #e1e9ef;border-radius:8px;font-size:11px;color:#60788e}.psiOptSignalGrid b{display:block;margin-top:4px;color:#183d5c}
 .psiOptTableWrap{overflow:auto}.psiOptTable{width:100%;border-collapse:collapse;font-size:12px}.psiOptTable th,.psiOptTable td{padding:10px;border-bottom:1px solid #e7edf2;text-align:left;white-space:nowrap}.psiOptTable th{background:#f4f8fb;color:#536b7e}.psiOptTable td[colspan]{text-align:center;color:#71879a}
 .psiOptFooter{margin-top:12px;padding:11px 13px;border-radius:9px;background:#eaf2f8;color:#39566e;font-size:12px;line-height:1.5}
 @media(max-width:760px){#psiOptionsWorkspace{padding:11px}.psiOptHead{align-items:flex-start;flex-direction:column}.psiOptHead h2{font-size:20px}.psiOptGrid,.psiOptInputs,.psiOptMetrics{grid-template-columns:1fr 1fr}.psiOptSignalGrid{grid-template-columns:1fr 1fr}}
 @media(max-width:420px){.psiOptInputs,.psiOptMetrics{grid-template-columns:1fr}}\`;
 document.head.appendChild(style);
 tab.addEventListener('click',()=>{const open=panel.hidden;panel.hidden=!open;tab.classList.toggle('active',open);if(open)panel.scrollIntoView({behavior:'smooth',block:'start'});});
 window.psiOptionsSignals=Object.freeze({mode:'READ_ONLY',orderPlacementEnabled:false,brokerStatus:'NOT_CONFIGURED',liveSignalsEnabled:false});
};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();