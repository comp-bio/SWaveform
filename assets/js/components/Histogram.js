import React from 'react';
const d3 = require('d3');

class Histogram extends React.Component {
  constructor(props) {
    super(props);
    this.ref = React.createRef();
    this.width = 128;
    this.height = 64;
    this.obj = props.obj;
    this.plot_width = 0;
    this.plot_height = 0;
  }
  
  zeroBorders(info) {
    let values = [{x: 0, y: 0}];
    for (let i = 0; i < this.plot_width; i++) {
      values.push({'x': i + 1, 'y': info.hist[i]});
    }
    values.push({x: values.length + 1, y: 0});
    return values;
  }

  componentDidMount() {
    const svg = d3.select(this.ref.current);
  
    Object.keys(this.obj).map(side => {
      const info = this.obj[side];
      //console.log('info', info);
      for (let i = 0; i < info.hist.length - 1; i++) {
        if (info.hist[i] > info.count/10) this.plot_width = i;
        this.plot_height = d3.max([info.hist[i], this.plot_height]);
      }
    });
  
    let x = d3.scaleLinear().range([0, this.width]).domain([0, this.plot_width]);
    let y = d3.scaleLinear().range([this.height, 0]).domain([0, this.plot_height]);
  
    let aX = d3.axisBottom(x).ticks(3);
    svg.append('g')
      .attr('class', 'axis axis--x')
      .attr('transform', `translate(0, ${this.height})`)
      .call(aX);
  
    let line = d3.line().x(d => x(d.x)).y(d => y(d.y));
    Object.keys(this.obj).map(side => {
      const data = this.zeroBorders(this.obj[side]);
      svg.append('path')
        .datum(data)
        .attr('class', `coverage side-${side}`)
        .attr('d', line);
    });
  }

  render() {
    return <svg width={this.width} height={this.height} className={'hist-plot-svg'} ref={this.ref} />;
  }
}

export default Histogram;
