(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;root.PSICsvImport=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const MAX_BYTES=5*1024*1024,MAX_ROWS=10000;
function parseCsv(text){
 if(typeof text!=='string')throw Error('CSV content must be text');
 if(text.length>MAX_BYTES)throw Error('CSV exceeds 5 MB');
 const first=(text.split(/\r?\n/,1)[0]||'');let delim=',',best=-1;
 for(const d of [',',';','\t','|']){let n=0,q=false;for(let i=0;i<first.length;i++){if(first[i]==='"'){if(q&&first[i+1]==='"'){i++;continue;}q=!q;}else if(first[i]===d&&!q)n++;}if(n>best){best=n;delim=d;}}
 const rows=[];let row=[],field='',quoted=false;
 for(let i=0;i<text.length;i++){const c=text[i];if(quoted){if(c==='"'&&text[i+1]==='"'){field+='"';i++;}else if(c==='"')quoted=false;else field+=c;}else if(c==='"'&&field.length===0)quoted=true;else if(c===delim){row.push(field);field='';}else if(c==='\n'||c==='\r'){if(c==='\r'&&text[i+1]==='\n')i++;row.push(field);field='';if(row.some(x=>String(x).trim()!==''))rows.push(row);row=[];if(rows.length>MAX_ROWS+1)throw Error('CSV exceeds 10,000 data rows');}else field+=c;}
 if(quoted)throw Error('CSV contains an unclosed quoted field');if(field.length||row.length){row.push(field);if(row.some(x=>String(x).trim()!==''))rows.push(row);}
 if(rows.length<2)throw Error('CSV must contain a header and at least one data row');if(rows[0].length<2)throw Error('CSV header has too few columns');
 const width=Math.max(...rows.map(r=>r.length));return {delimiter:delim,headers:rows[0].map(x=>String(x).trim().replace(/^\uFEFF/,'')),rows:rows.slice(1).map(r=>Array.from({length:width},(_,i)=>String(r[i]??'').trim()))};
}
function norm(s){return String(s??'').toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]/g,'');}
function symbolNorm(s){let x=String(s??'').trim().toUpperCase().replace(/\.(NS|BO)$/,'').replace(/^(NSE|BSE)[:\-]/,'').replace(/\s+/g,'');if(!x||/^(NA|N\/A|NULL|NONE|—|-)$/.test(x))return '';const compact=x.replace(/[^A-Z0-9]/g,'');const aliases={INFOSYS:'INFY',TATACONSULTANCY:'TCS',TATACONSULTANCYSERVICES:'TCS',HCLTECHNOLOGIES:'HCLTECH',TECHMAHINDRA:'TECHM',STATEBANKOFINDIA:'SBIN'};return aliases[compact]||x;}
function strictNumber(raw,header,key,source){
 let s=String(raw??'').trim();if(!s||/^(—|–|-|--|NA|N\/A|NULL)$/i.test(s))return null;
 const neg=s.startsWith('(')&&s.endsWith(')');if(neg)s=s.slice(1,-1).trim();
 const hasCr=/\bcr\b|crore/i.test(s);s=s.replace(/[₹$]/g,'').replace(/\bRs\.?\s*/ig,'').replace(/,/g,'').replace(/%/g,'').trim();
 const suffixCr=/\s*(?:cr\.?|crore?s?)$/i.test(s);if(suffixCr)s=s.replace(/\s*(?:cr\.?|crore?s?)$/i,'').trim();
 if(!/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/.test(s))return null;let n=Number(s);if(!Number.isFinite(n))return null;if(neg)n=-Math.abs(n);
 if(key==='marketCap'){const h=norm(header);const hasUnit=/cr|crore/.test(h)||hasCr||suffixCr;const knownScreener=source==='Screener.in CSV'&&/marketcapitalization|marketcap/.test(h);if(!hasUnit&&!knownScreener)return null;}
 if(['netProfit','operatingProfit'].includes(key)&&!/cr|crore/i.test(header)&&!hasCr&&!suffixCr&&source!=='Screener.in CSV')return null;
 if(['price','marketCap','bookValue','faceValue','high52','low52','dma50','dma200'].includes(key)&&n<=0)return null;
 if(['dividendYield','roce','roe','opm','sales3y','profit3y','promoter','pledged','public','rsi14'].includes(key)&&(n<0||n>100))return null;
 if(key==='piotroski'&&(n<0||n>9||!Number.isInteger(n)))return null;
 if(key==='peg'&&n<0)return null;
 if(key==='volume'&&n<0)return null;return n;
}
const fields=[
 {key:'price',names:['currentprice','currentpriceinrs','cmprs','cmp','lastprice','lasttradedprice']},
 {key:'marketCap',names:['marketcapitalization','marketcaprscrores','marketcaprscr','marketcapcr','marcaprsc','marketcap','mktcaprsc']},
 {key:'pe',names:['stockpe','pe','pettm','priceearnings','priceearningsratio','petr']},
 {key:'bookValue',names:['bookvalue','bookvalueinrs','bv']},
 {key:'dividendYield',names:['dividendyield','divyld','divyield']},
 {key:'roce',names:['roce','returnoncapitalemployed']},
 {key:'roe',names:['roe','returnonequity']},
 {key:'debtEquity',names:['debtequity','debttoequity','debttoequityratio']},
 {key:'eps',names:['epsinrs','eps','earningspershare','earningspershareinrs']},
 {key:'netProfit',names:['netprofit','netprofitrscrore','profitaftertax','pat']},
 {key:'operatingProfit',names:['operatingprofit','operatingprofitrscrore']},
 {key:'opm',names:['opm','opmpercent','operatingprofitmargin']},
 {key:'sales3y',names:['salesgrowth3years','salesgrowth3y','sales3ycagr','salescagr3y']},
 {key:'profit3y',names:['profitgrowth3years','profitgrowth3y','profit3ycagr','profitcagr3y']},
 {key:'promoter',names:['promoterholding','promotersholding','promoterpercentage','promoterstake']},
 {key:'pledged',names:['pledgedpercentage','promoterpledged','pledged']},
 {key:'currentRatio',names:['currentratio']},
 {key:'interestCoverage',names:['interestcoverage','interestcoverageratio']},
 {key:'industryPE',names:['industrype','industrypriceearnings']},
 {key:'high52',names:['52weekhigh','week52high','high52week','high52','highlowhigh','high52w']},
 {key:'low52',names:['52weeklow','week52low','low52week','low52','highlowlow','low52w']},
 {key:'faceValue',names:['facevalue','facevalueinrs','fv']},
 {key:'piotroski',names:['piotroskiscrore','piotroskiscore','piotroski']},
 {key:'peg',names:['pegratio','peg']},
 {key:'dma200',names:['dma200','200dma','200daymovingaverage','dma200inrs']},
 {key:'dma50',names:['dma50','50dma','50daymovingaverage','dma50inrs']},
 {key:'public',names:['publicholding','publicshareholding','publicholdingpercentage','publicshareholdingpercentage']},
 {key:'rsi14',names:['rsi14','rsi']},
 {key:'profitVariance3y',names:['profitvar3yrs','profitvar3years','profitvariance3yrs','profitvariance3years']}
];
function findIndex(headers,names){const norms=headers.map(norm);for(const n of names){const i=norms.findIndex(x=>x===n);if(i>=0)return i;}return -1;}
function parseDate(s){const v=String(s??'').trim();if(!v)return null;let d=new Date(v);if(Number.isFinite(d.getTime()))return d.getTime();let m=v.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})$/);if(m){d=new Date(Number(m[3]),Number(m[2])-1,Number(m[1]));return Number.isFinite(d.getTime())?d.getTime():null;}m=v.match(/^(\d{1,2})[-\s]([A-Za-z]{3})[-\s](\d{4})$/);if(m){d=new Date(`${m[2]} ${m[1]}, ${m[3]} 00:00:00`);return Number.isFinite(d.getTime())?d.getTime():null;}return null;}
function unitFor(key,header,source){if(key==='marketCap'||['netProfit','operatingProfit'].includes(key))return (/cr|crore/i.test(header)||(source==='Screener.in CSV'&&/marketcapitalization|marketcap|netprofit|operatingprofit/.test(norm(header))))?'INR_CRORE':'PROVIDER_UNIT_NOT_VERIFIED';if(['price','eps','bookValue','faceValue','high52','low52','dma50','dma200'].includes(key))return 'INR_PER_SHARE';if(['dividendYield','roce','roe','opm','sales3y','profit3y','promoter','pledged','public','profitVariance3y'].includes(key))return 'PERCENT';if(['pe','industryPE','debtEquity','currentRatio','interestCoverage','peg'].includes(key))return 'RATIO';if(key==='rsi14')return 'INDEX_0_100';if(key==='piotroski')return 'SCORE_0_9';return 'PROVIDER_UNIT_NOT_VERIFIED';}
function parseImportCsv(text,opts){
 opts=opts||{};const source=String(opts.source||'User CSV');const parsed=parseCsv(text);const headers=parsed.headers;const idx=(names)=>findIndex(headers,names);
 const symbolI=idx(['nsecode','nsesymbol','symbol','ticker','exchangecode','nse','tckrsymb','tradingsymbol']);const bseI=idx(['bsecode','bsesymbol']);const periodI=idx(['period','reportingperiod','fiscalperiod','financialyear','fy','asofperiod']);
 const dateI=idx(['date','datetime','timestamp','tradedate','tradingdate','tradt','tradgdate']);const openI=idx(['open','openprice','opnpric']);const highI=idx(['high','highprice','hghpric']);const lowI=idx(['low','lowprice','lwpric']);const closeI=idx(['close','closeprice','closingprice','adjclose','adjustedclose','clspric']);const volumeI=idx(['volume','sharestraded','tradedvolume','ttltradgvol','ttltrdqnty']);
 const isOHLCV=dateI>=0&&openI>=0&&highI>=0&&lowI>=0&&closeI>=0&&volumeI>=0;const mappings=[];for(const def of fields){const i=findIndex(headers,def.names);if(i>=0)mappings.push({key:def.key,index:i,header:headers[i]});}
 if(!mappings.length&&!isOHLCV)throw Error('No recognized financial metric headers. Supported fields include CMP, market cap (₹ Cr), PE, EPS, ROCE, ROE, debt/equity, dividend yield, book value, and OHLCV.');
 const records=[],warnings=[];for(const row of parsed.rows){let symbol=symbolNorm(symbolI>=0?row[symbolI]:bseI>=0?row[bseI]:'');if(!symbol&&parsed.rows.length===1&&opts.selectedSymbol)symbol=symbolNorm(opts.selectedSymbol);if(!symbol&&!isOHLCV)continue;const out={symbol,fields:{},meta:{},period:periodI>=0&&row[periodI]?row[periodI]:'UNSPECIFIED_IN_EXPORT'};for(const m of mappings){const value=strictNumber(row[m.index],m.header,m.key,source);if(value===null)continue;out.fields[m.key]=value;out.meta[m.key]={source,header:m.header,unit:unitFor(m.key,m.header,source),period:out.period};}if(symbol&&Object.keys(out.fields).length)records.push(out);}
 const counts={};for(const r of records)counts[r.symbol]=(counts[r.symbol]||0)+1;const duplicates=Object.keys(counts).filter(k=>counts[k]>1);if(duplicates.length){warnings.push('Duplicate symbol rows skipped as ambiguous: '+duplicates.join(', '));for(let i=records.length-1;i>=0;i--)if(duplicates.includes(records[i].symbol))records.splice(i,1);}
 if(symbolI<0&&bseI<0&&parsed.rows.length>1&&!isOHLCV)warnings.push('Rows without exchange symbols were skipped; no fuzzy company-name mapping was attempted.');
 let historyRows=[],historyPeriod='UNSPECIFIED_IN_EXPORT',historySymbol=symbolNorm(opts.selectedSymbol);
 if(isOHLCV){const symbolValues=[...new Set(parsed.rows.map(row=>symbolNorm(symbolI>=0?row[symbolI]:'')).filter(Boolean))];if(!historySymbol&&symbolValues.length===1)historySymbol=symbolValues[0];const allowed=historySymbol||null;const seen=new Set();for(const row of parsed.rows){const rowSymbol=symbolNorm(symbolI>=0?row[symbolI]:'');if(allowed&&rowSymbol&&rowSymbol!==allowed)continue;if(!allowed&&symbolValues.length>1)continue;const t=parseDate(row[dateI]);if(!t)continue;const vals=[openI,highI,lowI,closeI].map(i=>strictNumber(row[i],headers[i],'price',source));const volume=strictNumber(row[volumeI],headers[volumeI],'volume',source);if(vals.some(v=>v===null)||volume===null||volume<0)continue;const [open,high,low,close]=vals;if(high<Math.max(open,close,low)||low>Math.min(open,close,high))continue;const key=String(t);if(seen.has(key))continue;seen.add(key);historyRows.push({time:t,date:t,open,high,low,close,volume});}historyRows.sort((a,b)=>a.time-b.time);if(historyRows.length<20)warnings.push('Historical OHLCV import has fewer than 20 valid bars; technical indicators may be incomplete.');if(symbolValues.length>1&&!allowed)warnings.push('Multiple symbols were found in this OHLCV file. Select a symbol before importing; mixed-symbol candles were rejected.');if(allowed&&symbolValues.length>1)warnings.push('OHLCV rows were filtered to '+allowed+'; rows for other symbols were excluded.');}
 if(!records.length&&!historyRows.length)throw Error('No valid symbol/metric rows or valid OHLCV bars were found. Check symbol codes, dates, and numeric fields.');
 return {source,records,historyRows,historySymbol,historyPeriod,totalFields:mappings.length,mappedHeaders:mappings.map(m=>`${headers[m.index]} → ${m.key}`),warnings,delimiter:parsed.delimiter};
}
return {parseCsv,parseImportCsv,norm,symbolNorm,strictNumber,unitFor};
});
