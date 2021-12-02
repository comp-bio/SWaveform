import React from 'react';
import overview from "../../../build/overview.json";
const d3 = require('d3');

const gradients = {
  'gpos25':  {'3':  '#C8C8C8', '15': '#e6e6e6', '60': '#ccc'},
  'gpos50':  {'3':  '#AAA',    '15': '#BBB',    '66': '#999'},
  'gpos75':  {'3':  '#999',    '15': '#999',    '66': '#777'},
  'gpos100': {'3':  '#777',    '15': '#999',    '66': '#444'},
  'acen':    {'3':  '#FEE',    '15': '#FEE',    '66': '#FDD'},
  'gneg':    {'70': '#FFF',    '95': '#e6e6e6', '100': '#FFF'},
};

function KaryotypeBar(el, parent) {
  const node = d3.select(el).node();
  if (!node) return ;

  console.log('Karyotype [+]');

  let state = parent.state;
  const width = node.getBoundingClientRect().width;
  const map = parent.karyotype[state.chr] || [];
  const centre = map.filter(box => box[3] === 'acen');
  const chr_size = map[map.length - 1][1];

  if (centre.length === 0) return;

  let x = d3.scaleLinear().range([0, width]).domain([0, chr_size]);
  let y = d3.scaleLinear().range([60, 0]).domain([0, 20]);
  let axis = d3.axisBottom(x);

  if (parent.state.windowWidth < window.sizes.M) {
    axis.ticks(3);
  }

  d3.select(el).html('');
  const svg = d3.select(el).append('svg')
    .attr('overflow', 'visible')
    .attr('class', 'karyotype-svg')
    .attr('viewBox', [0, 0, width, 120]);

  const bands = svg.append('g')
    .attr('clip-path', 'url(#chromosome-cp)')
    .attr('class', 'bands');

  const defs = svg.append('defs');

  svg.append('g')
    .attr('class', 'axis axis--x')
    .attr('transform', `translate(0, 100)`)
    .call(axis);

  const cen = x(centre[0][1]);
  const end = x(chr_size);
  const left  = `M4,3 L${cen-4-1},3 Q${cen+4-1},15,${cen-4-1},27 L4,27 Q-4,15,4,3`;
  const right = `M${cen+4},3 L${end-4+1},3 Q${end+4+1},15,${end-4+1},27 L${cen+4},27 Q${cen-4},15,${cen+4},3`;

  svg.append('path').attr('class', 'chr-border').attr('d', left);
  svg.append('path').attr('class', 'chr-border').attr('d', right);

  const pattern = defs.append('pattern')
    .attr('width', '2')
    .attr('height', '1')
    .attr('patternUnits', 'userSpaceOnUse')
    .attr('patternTransform', 'rotate(-30 0 0)')
    .attr('id', 'gvar');
  pattern.append('rect').attr('x', 0).attr('y', 0);
  pattern.append('line').attr('x1', 0).attr('y1', 0).attr('x2', 0).attr('y2', '100%');

  const cp = defs.append('svg:clipPath').attr('id', 'chromosome-cp');
  cp.append('path').attr('d', left);
  cp.append('path').attr('d', right);

  const density = svg.append('g')
    .attr('transform', `translate(0, 35)`)
    .attr('class', 'density');

  const notes = svg.append('g')
    .attr('class', 'notes');

  for (let k in gradients) {
    const gradient = defs.append('linearGradient')
      .attr('id', k)
      .attr('x1', 0).attr('y1', 0)
      .attr('x2', 0).attr('y2', '100%');
    for (let offset in gradients[k]) {
      gradient.append('stop')
        .attr('offset', `${offset}%`)
        .attr('stop-color', gradients[k][offset]);
    }
  }

  let last_hint = -30;
  map.map(box => {
    const dx = parseFloat(x(box[0]));
    const width = x(box[1] - box[0]);
    const mean = parseFloat(x(box[1]/2 + box[0]/2));

    bands.append('rect')
      .attr('transform', `translate(${dx}, 3)`)
      .attr('width', width)
      .attr('height', 24)
      .attr('fill', `url(#${box[3]})`)
      .attr('class', box[3]);

    if (width > 38 || (mean - 38) > last_hint) {
      last_hint = mean;

      notes.append('line')
        .attr('class', 'karyo-hints')
        .attr('x1', mean).attr('y1', -4)
        .attr('x2', mean).attr('y2', 8);

      notes.append('text')
        .attr('class', 'karyo-hints')
        .attr('x', mean - (box[2].length) * 5.1 / 2).attr('y', -8)
        .text(box[2]);
    }
  });

  // Density
  Object.keys(parent.overview['ds'] || {}).map(ds => {
    let line = d3.line().x(d => x(d[0])).y(d => y(d[1]));
    let density_line = density.append('path')
        .datum([])
        .attr('class', 'density')
        .attr('fill', parent.ds_color(ds))
        .attr('fill-opacity', state.datasets[ds] ? 0.7 : 0.2)
        .attr('d', line);

    const dens = parent.overview['ds'][ds].density[state.chr];
    const m = d3.max(dens.l) * 0.5;

    let v = dens.l.map((v, i) => [i * dens.step + 1, v > m ? m : v]);
    v.unshift([0,0]);
    v.push([dens.l.length * dens.step, 0]);

    y.domain([0, m]);
    density_line.datum(v).attr('d', line);
  });


  // Cursor events
  let brush = d3.brushX()
    .extent([[0, 1], [width + 1, 100]])
    .on('brush end', brushed);

  const brushNode = svg.append('g')
    .attr('class', 'selection')
    .call(brush);

  set(state);

  function set(state) {
    brushNode.call(brush.move, [x(state.start), x(state.end)]);
  }

  function validate(s) {
    const width = 100000;
    if (s.end - s.start < width) {
      let m = Math.round(s.end/2 + s.start/2);
      s = {'start': m - width/2, 'end': m + width/2};
    }
    s.start = Math.max(0, Math.min(s.start, chr_size - width));     // 0 <= start <= chrSize - width
    s.end   = Math.min(chr_size, Math.max(s.start + width, s.end)); // start + width <= end <= chrSize
    return s;
  }

  function brushed(e){
    if (!e.selection) {
      let c = x.invert(e.sourceEvent.offsetX);
      let s = validate({'start': c, 'end': c});
      return brushNode.call(brush.move, [x(s.start), x(s.end)]);
    }

    let bp = e.selection.map(e => Math.round(x.invert(e)));
    parent.onPositionChange(bp, e.type);
  }

  return { set, validate };
}

export default KaryotypeBar;