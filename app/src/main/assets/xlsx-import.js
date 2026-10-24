(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;root.PSIXlsxImport=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const MAX_BYTES=5*1024*1024,MAX_ENTRIES=2000;
function xmlText(s){return String(s||'').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&apos;/g,"'").replace(/&amp;/g,'&');}
function attr(s,k){const m=String(s||'').match(new RegExp('(?:^|\\\\s)'+k+'="([^"]*)"'));return m?xmlText(m[1]):'';}
function colIndex(ref){const m=String(ref||'').match(/^([A-Z]+)/);if(!m)return 0;let n=0;for(const c of m[1])n=n*26+c.charCodeAt(0)-64;return n-1;}
async function unzip(buf){
 const u=new Uint8Array(buf),v=new DataView(buf);let eocd=-1;
 for(let i=u.length-22;i>=Math.max(0,u.length-65557);i--){if(v.getUint32(i,true)===0x06054b50){eocd=i;break;}}
 if(eocd<0)throw Error('This XLSX file is not a valid ZIP workbook.');
 const count=v.getUint16(eocd+10,true),cd=v.getUint32(eocd+16,true);if(count>MAX_ENTRIES)throw Error('Workbook has too many ZIP entries.');
 const files={};let p=cd;
 for(let n=0;n<count;n++){
  if(v.getUint32(p,true)!==0x02014b50)throw Error('Invalid XLSX directory entry.');
  const method=v.getUint16(p+10,true),csize=v.getUint32(p+20,true),nameLen=v.getUint16(p+28,true),extraLen=v.getUint16(p+30,true),commentLen=v.getUint16(p+32,true),local=v.getUint32(p+42,true);
  const name=new TextDecoder().decode(u.slice(p+46,p+46+nameLen));p+=46+nameLen+extraLen+commentLen;
  if(name.endsWith('/'))continue;
  if(csize>MAX_BYTES)throw Error('XLSX entry exceeds the 5 MB safety limit.');
  if(v.getUint32(local,true)!==0x04034b50)throw Error('Invalid XLSX local file header: '+name);
  const start=local+30+v.getUint16(local+26,true)+v.getUint16(local+28,true),compressed=u.slice(start,start+csize);let bytes;
  if(method===0)bytes=compressed;else if(method===8){if(typeof DecompressionStream==='undefined')throw Error('This WebView cannot decompress XLSX. Please export as CSV.');const ds=new DecompressionStream('deflate-raw');const stream=new Blob([compressed]).stream().pipeThrough(ds);bytes=new Uint8Array(await new Response(stream).arrayBuffer());}else throw Error('Unsupported XLSX compression method '+method+'.');
  if(bytes.length>MAX_BYTES)throw Error('Expanded workbook entry exceeds the safety limit.');
  files[name]=new TextDecoder('utf-8').decode(bytes);
 }
 return files;
}
function textRuns(xml){return Array.from(String(xml||'').matchAll(/<t(?:\s[^>]*)?>([\s\S]*?)<\/t>/g),m=>xmlText(m[1])).join('');}
function sheetRows(xml,shared){
 const rows=[];for(const rm of String(xml||'').matchAll(/<row\b[^>]*>([\s\S]*?)<\/row>/g)){const cells=[];for(const cm of rm[1].matchAll(/<c\b([^>]*)>([\s\S]*?)<\/c>/g)){const a=cm[1],body=cm[2],ref=attr(a,'r'),type=attr(a,'t'),idx=colIndex(ref);let value='';if(type==='s'){const m=body.match(/<v>([\s\S]*?)<\/v>/);value=m?shared[Number(m[1])]||'':'';}else if(type==='inlineStr'){value=textRuns(body);}else{const m=body.match(/<v>([\s\S]*?)<\/v>/);value=m?xmlText(m[1]):'';}cells[idx]=value;}rows.push(cells);}return rows;
}
async function parseWorkbook(buffer,opts){
 opts=opts||{};if(!buffer||buffer.byteLength<100)throw Error('XLSX workbook is empty or invalid.');if(buffer.byteLength>MAX_BYTES)throw Error('XLSX exceeds 5 MB. Export fewer columns/rows and retry.');
 const files=await unzip(buffer),wb=files['xl/workbook.xml'],rels=files['xl/_rels/workbook.xml.rels'];if(!wb||!rels)throw Error('Workbook metadata is missing.');
 const targets={};for(const m of rels.matchAll(/<Relationship\b([^>]*)\/?>/g)){const a=m[1];targets[attr(a,'Id')]=attr(a,'Target').replace(/^\//,'').replace(/^xl\//,'');}
 const sheets={};for(const m of wb.matchAll(/<sheet\b([^>]*)\/?>/g)){const name=attr(m[1],'name'),rid=attr(m[1],'r:id');let target=targets[rid]||'';if(target&&!target.startsWith('xl/'))target='xl/'+target;sheets[name]=target;}
 const shared=[];if(files['xl/sharedStrings.xml'])for(const m of files['xl/sharedStrings.xml'].matchAll(/<si\b[^>]*>([\s\S]*?)<\/si>/g))shared.push(textRuns(m[1]));
 let dataPath=Object.entries(sheets).find(([n])=>n.trim().toLowerCase()==='data sheet')?.[1];if(!dataPath)throw Error('Screener workbook has no "Data Sheet" tab. Export the original Screener Excel workbook.');
 const rows=sheetRows(files[dataPath],shared),labelMap=new Map();for(const row of rows){const label=String(row[0]||'').trim();if(label)labelMap.set(label.toLowerCase(),row);}
 const get=(label,col=1)=>{const r=labelMap.get(label.toLowerCase());return r?String(r[col]??'').trim():'';};
 const company=get('COMPANY NAME');if(!company)throw Error('Screener Data Sheet has no company name.');
 const compact=company.toUpperCase().replace(/[^A-Z0-9]/g,'');const aliases={COLGATEPALMOLIVEINDIALTD:'COLPAL',COLGATEPALMOLIVEINDIA:'COLPAL',INFOSYSLIMITED:'INFY',TATACONSULTANCYSERVICES:'TCS'};let symbol=aliases[compact]||'';
 if(!symbol){const selected=String(opts.selectedSymbol||'').trim().toUpperCase().replace(/\.(NS|BO)$/,'');if(selected)symbol=selected;else throw Error('Cannot safely map "'+company+'" to an NSE symbol. Select the matching stock before import.');}
 const num=x=>{if(x===null||x===undefined||String(x).trim()==='')return null;const n=Number(String(x).replace(/,/g,''));return Number.isFinite(n)?n:null;};
 const fields={},meta={},source=String(opts.source||'Screener.in Excel export');
 function put(key,val,unit,period,header){if(val===null||!Number.isFinite(val))return;fields[key]=val;meta[key]={source,header,unit,period:period||'UNSPECIFIED_IN_EXPORT'};}
 const price=num(get('Current Price')),cap=num(get('Market Capitalization')),shares=num(get('Adjusted Equity Shares in Cr',10));
 const findRow=(label,start,end)=>{for(let i=start;i<Math.min(end,rows.length);i++)if(String(rows[i][0]||'').trim().toLowerCase()===label.toLowerCase())return rows[i];return [];};
 const annualDates=findRow('Report Date',15,40),annualSales=findRow('Sales',15,40),annualProfit=findRow('Net profit',15,40);
 const latestAnnualCol=10;const latestAnnualDate=String(annualDates[latestAnnualCol]||'').slice(0,10)||'LATEST_ANNUAL_PERIOD_IN_EXPORT';
 const quarterDates=findRow('Report Date',40,55),quarterSales=findRow('Sales',40,55),quarterProfit=findRow('Net profit',40,55);
 const latestQuarterCol=10,qSales=num(quarterSales[latestQuarterCol]),qNet=num(quarterProfit[latestQuarterCol]);
 const annualComponent=(label)=>findRow(label,15,40);const rawMaterial=annualComponent('Raw Material Cost'),changeInventory=annualComponent('Change in Inventory'),powerFuel=annualComponent('Power and Fuel'),otherMfr=annualComponent('Other Mfr. Exp'),employeeCost=annualComponent('Employee Cost'),sellingAdmin=annualComponent('Selling and admin'),otherExpenses=annualComponent('Other Expenses');
 const componentValues=[rawMaterial,changeInventory,powerFuel,otherMfr,employeeCost,sellingAdmin,otherExpenses].map(r=>num(r[latestAnnualCol]));
 const annualOPValue=componentValues.every(v=>v!==null)&&num(annualSales[latestAnnualCol])!==null?num(annualSales[latestAnnualCol])-(componentValues[0]+componentValues[2]+componentValues[3]+componentValues[4]+componentValues[5]+componentValues[6]-componentValues[1]):null;
 put('price',price,'INR_PER_SHARE','WORKBOOK_META','Current Price');
 put('marketCap',cap,'INR_CRORE','WORKBOOK_META','Market Capitalization');
 const eps=(num(annualProfit[latestAnnualCol])!==null&&shares>0)?num(annualProfit[latestAnnualCol])/shares:null;
 put('eps',eps,'INR_PER_SHARE',latestAnnualDate,'Derived: latest annual net profit / adjusted equity shares');
 put('netProfit',num(annualProfit[latestAnnualCol]),'INR_CRORE',latestAnnualDate,'Net profit');
 put('operatingProfit',annualOPValue,'INR_CRORE',latestAnnualDate,'Derived from Screener Data Sheet expense components');
 const sales=num(annualSales[latestAnnualCol]),op=annualOPValue;
 put('opm',sales>0&&op!==null?op/sales*100:null,'PERCENT',latestAnnualDate,'Derived: operating profit / sales');
 put('pe',price>0&&eps>0?price/eps:null,'RATIO',latestAnnualDate,'Derived: workbook current price / latest annual EPS');
 // Include the latest quarterly snapshot as explicitly labelled metadata; do not treat it as live market data.
 const period=latestAnnualDate;
 if(!Object.keys(fields).length)throw Error('No supported metrics were found in the Screener workbook.');
 const records=[{symbol,fields,meta,period,companyName:company,quarterlySummary:{period:String(quarterDates[latestQuarterCol]||'UNSPECIFIED_IN_EXPORT'),sales:qSales,netProfit:qNet}}];
 const warnings=['Imported from Screener Data Sheet; not a live quote.','Only metrics present or safely derivable from this workbook are mapped.','Quarterly statements remain in the workbook; this import does not create OHLCV candles.'];
 return {source,records,historyRows:[],historySymbol:symbol,historyPeriod:'UNAVAILABLE_IN_WORKBOOK',totalFields:Object.keys(fields).length,mappedHeaders:Object.keys(meta).map(k=>meta[k].header+' → '+k),warnings,workbookSheets:Object.keys(sheets),companyName:company};
}
return {parseWorkbook};
});