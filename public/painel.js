
// Painel Oracular v1 — modo Autônomo (sem OAuth)
// Requer: dados_oraculares.json na mesma pasta.

const $ = (s) => document.querySelector(s);
const fmt = new Intl.NumberFormat('pt-BR');
const fmtPct = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });

let dadosGlobais = null;

async function carregarDados(arquivo = 'dados_oraculares.json') {
  const res = await fetch(arquivo + '?t=' + Date.now());
  if (!res.ok) throw new Error('Falha ao carregar ' + arquivo);
  const data = await res.json();
  dadosGlobais = data;
  atualizarPainel(data);
}

function atualizarPainel(data) {
  // KPIs
  $('#kpi-impr').innerText = fmt.format(data.kpis.impressoes_30d);
  $('#kpi-cliques').innerText = fmt.format(data.kpis.cliques_30d);
  $('#kpi-ctr').innerText = fmtPct.format(data.kpis.ctr_medio_pct) + '%';
  $('#kpi-pos').innerText = data.kpis.posicao_media.toFixed(2);

  // Deltas
  $('#delta-impr').innerText = sinal(data.kpis.delta_impressoes_pct) + '% vs período anterior';
  $('#delta-cliques').innerText = sinal(data.kpis.delta_cliques_pct) + '% vs período anterior';
  $('#delta-ctr').innerText = sinal(data.kpis.delta_ctr_pp, true) + ' pp';
  $('#delta-pos').innerText = sinal(data.kpis.delta_posicao_pp, true) + ' melhor';

  // Última atualização
  $('#ultima-atualizacao').innerText = data.meta.ultima_atualizacao;
  $('#periodo').innerText = `${data.meta.periodo.inicio} — ${data.meta.periodo.fim}`;

  // Série temporal
  desenharSerie(data);

  // Dispositivos
  desenharDonut(data);

  // Países
  preencherTabelaPaises(data.paises);
}

function sinal(v, pp=false){
  const pre = v>0? '+':'';
  const num = (pp? v.toFixed(1) : v.toFixed(0)).replace('.',',');
  return pre + num;
}

function preencherTabelaPaises(paises){
  const tbody = $('#tbody-paises');
  tbody.innerHTML = '';
  for(const p of paises){
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${p.pais}</td>
      <td>${fmt.format(p.impressoes)}</td>
      <td>${fmt.format(p.cliques)}</td>
      <td>${fmtPct.format(p.ctr_pct)}%</td>
    `;
    tbody.appendChild(tr);
  }
}

// ----- Charts (Chart.js via CDN) -----
let linhaChart = null;
let donutChart = null;

function desenharSerie(data){
  const ctx = $('#chart-serie').getContext('2d');
  if(linhaChart) linhaChart.destroy();
  linhaChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.series.datas,
      datasets: [
        { label:'Cliques', data: data.series.cliques, borderWidth:2, tension:.3 },
        { label:'Impressões', data: data.series.impressoes, borderWidth:2, tension:.3, yAxisID:'y1' },
        { label:'CTR (%)', data: data.series.ctr_pct, borderWidth:2, tension:.3, yAxisID:'y2' }
      ]
    },
    options: {
      responsive:true,
      scales:{
        y: { beginAtZero:true },
        y1: { beginAtZero:true, position:'right' },
        y2: { beginAtZero:false, position:'right' }
      },
      plugins:{
        legend:{ labels:{ color:'#dbe7f4' } }
      }
    }
  });
}

function desenharDonut(data){
  const ctx = $('#chart-donut').getContext('2d');
  if(donutChart) donutChart.destroy();
  const d = data.dispositivos;
  donutChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['desktop','mobile','tablet'],
      datasets: [{ data: [d.desktop, d.mobile, d.tablet] }]
    },
    options: { plugins:{ legend:{ labels:{ color:'#dbe7f4' } } } }
  });
}

// ----- Atualização manual do arquivo -----
function acionarFilePicker(){
  $('#filePicker').click();
}

function carregarArquivoLocal(ev){
  const file = ev.target.files[0];
  if(!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try{
      const data = JSON.parse(reader.result);
      dadosGlobais = data;
      atualizarPainel(data);
      toast('Base atualizada a partir do arquivo local.');
    }catch(e){
      alert('Arquivo inválido. Certifique-se de que é um JSON compatível.');
    }
  };
  reader.readAsText(file, 'utf-8');
}

// ---- feedback mínimo ----
function toast(msg){
  const el = document.createElement('div');
  el.textContent = msg;
  el.style.position='fixed'; el.style.bottom='24px'; el.style.left='50%'; el.style.transform='translateX(-50%)';
  el.style.background='#1b2028'; el.style.color='#dbe7f4'; el.style.padding='10px 14px'; el.style.border='1px solid #2b3340';
  el.style.borderRadius='10px'; el.style.boxShadow='0 10px 30px rgba(0,0,0,.35)';
  document.body.appendChild(el);
  setTimeout(()=> el.remove(), 1800);
}

// Init
window.addEventListener('DOMContentLoaded', ()=>{
  carregarDados().catch(err=> alert('Erro ao carregar base: ' + err.message));
  $('#btnAtualizar').addEventListener('click', acionarFilePicker);
  $('#filePicker').addEventListener('change', carregarArquivoLocal);
});
