import React from 'react';
const d3 = require('d3');

class Signal extends React.Component {
  constructor(props) {
    super(props);
    this.ref = React.createRef();
    this.width = 261;
    this.obj = props.obj;

    if (props.parent.state.windowWidth < window.sizes.M) {
      this.width = (props.parent.state.windowWidth - 12 * 4) / 3;
    }
    if (props.parent.state.windowWidth < window.sizes.S) {
      this.width = (props.parent.state.windowWidth - 12 * 3) / 2;
    }
    if (props.parent.state.windowWidth < window.sizes.XS) {
      this.width = props.parent.state.windowWidth - 12 * 2;
    }
  }

  componentDidMount() {
    const svg = d3.select(this.ref.current);

    let cov = this.obj.coverage;
    let x = d3.scaleLinear().range([0, this.width]).domain([this.obj.start, this.obj.end]);
    let y = d3.scaleLinear().range([100, 0]).domain([0, d3.max([...cov, this.obj.meancov]) + 5]);
    let ySAX = d3.scaleLinear().range([100, 0]).domain([0, 32]);

    // Density
    let line = d3.line().x(d => x(d.x)).y(d => y(d.y));
    let density_line = svg.append('path')
      .datum([])
      .attr('class', 'coverage')
      .attr('d', line);
  
    let lineSAX = d3.line().x(d => x(d.x * 512/64)).y(d => y(d.y));
    let density_line_SAX = svg.append('path')
      .datum([])
      .attr('class', 'coverage-sax')
      .attr('d', lineSAX);
  
    const m = y(this.obj.meancov);
    svg.append('line')
      .attr('class', 'mean-line')
      .attr('x1', 0).attr('x2', this.width).attr('y1', m).attr('y2', m);
    svg.append('line')
      .attr('class', 'v-line')
      .attr('x1', this.width/2).attr('x2', this.width/2).attr('y1', 0).attr('y2', 100);

    let aX = d3.axisBottom(x).ticks(3);
    let aY = d3.axisLeft(y).ticks(6);
  
    let SAX_cnt = svg.append('g')
      .attr('class', 'sax-plot')
      .attr('transform', `translate(0, 0)`);

    svg.append('g')
      .attr('class', 'axis axis--x')
      .attr('transform', `translate(0, 100)`)
      .call(aX);

    svg.append('g')
      .attr('class', 'axis axis--y')
      .attr('transform', `translate(${this.width}, 0)`)
      .call(aY);

    // let v = [];
    // let vSAX = [];

    let v = cov.map((v, i) => ({x: i + this.obj.start, y: v}));
    v.unshift({x: this.obj.start, y: 0});
    v.push({x: this.obj.start + cov.length - 1, y: 0});
    density_line.datum(v).attr('d', line);
  
    this.obj.sax.map((v, i) => {
      SAX_cnt.append('line')
        .attr('x1', x(this.obj.start + i * 512/64))
        .attr('x2', x(this.obj.start + (i+1) * 512/64))
        .attr('y1', ySAX(v))
        .attr('y2', ySAX(v))
    })
    // this.obj.sax
    //this.obj.sax
    let vSAX = cov.map((v, i) => ({x: i + this.obj.start, y: v}));
    density_line_SAX.datum(vSAX).attr('d', lineSAX);
  }

  render() {
    return <svg width={this.width} height={100} className={'signal-plot-svg'} ref={this.ref} />;
  }
}

export default Signal;
