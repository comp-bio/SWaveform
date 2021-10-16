import React from "react";
import Loader from "./Loader";
import KaryotypeBar from "./KaryotypeBar";
import Signal from "./Signal";

const karyotype = require('../../../data/GRCh38.json')
const overview = require('../../../data/overview.json')
const d3 = require('d3')

const types = Object.keys(overview['types']);
const type_color = d3.scaleOrdinal().domain(types).range(d3.schemeTableau10);
let timer = null;

class Plot extends React.Component {
  constructor(props) {
    super(props);
    this.karyotype = karyotype;
    this.overview = overview;

    this.state = {
      'chr': '1', 'start': 3000000, 'end': 3050000,
      'data:signal': [], 'types': {},
      'windowWidth': window.innerWidth
    };
    types.map(k => { this.state['types'][k] = true; });

    this.loader = new Loader(this);

    this.onResize = this.onResize.bind(this);
  }

  onResize(e) {
    this.setState({ windowWidth: window.innerWidth }, () => {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => {
        this.gmap = KaryotypeBar('#gmap', this);
      }, 400);
    });
  }

  onPositionChange(e, type) {
    this.setState({'start': e[0], 'end': e[1]}, () => {
      if (type === 'end') this.loader.get('signal');
    });
  }

  componentDidMount() {
    this.gmap = KaryotypeBar('#gmap', this);
    window.addEventListener("resize", this.onResize);
  }

  componentWillUnMount() {
    window.addEventListener("resize", this.onResize);
  }

  validate(force = true) {
    let state = this.gmap.validate({
      'start': parseInt(this.state.start) || 0,
      'end': parseInt(this.state.end) || 0
    });
    this.setState(state);
    if (force) this.gmap.set(state);
  }

  circle(name) {
    return (<span className={'circle'} style={{background: type_color(name)}} />)
  }

  selectChr(val) {
    let c = karyotype[val];
    const offset = 10 * 1000 * 1000;
    const center = Math.round(c[c.length - 1][1]/4);
    this.setState({
      'chr': val,
      'start': center - Math.min(offset, center),
      'end': center + Math.min(offset, center)
    }, () => {
      this.gmap = KaryotypeBar('#gmap', this);
    });
  }

  renderPosition(name) {
    return (
      <input value={this.state[name]}
             onChange={(e) => this.setState({[name]: e.target.value})}
             onBlur={(e) => this.validate()}
             type={'text'} className={'form-control'} />
    );
  }

  changeType(name) {
    this.setState(prevState => {
      prevState['types'][name] = !prevState['types'][name];
      return {'types': prevState['types']};
    }, () => {
      this.loader.get('signal');
    });
  }

  renderResult() {
    if (this.state['loading:signal']) {
      return (<div className={'placeholder'}>Loading...</div>);
    }

    if (this.state['data:signal'].length) {
      return this.state['data:signal'].map((e, k) => {
        return (
          <div className={'signal-wrapper'} key={k}>
            <div className={'hints'}>
              <span>{this.circle(e.type)} <span className={'tag'}>{e.type}</span> <span className={`tag side-${e.side}`}>{e.side}</span></span>
              <span><span className={'tag mini'}>{e.name}</span> <span className={'tag mini'}>{e.population}</span></span>
            </div>
            <Signal obj={e} parent={this} />
          </div>
        );
      });
    }

    return (<div className={'placeholder'}>No coverage signals loaded for this region</div>)
  }

  render() {
    return (
      <div>
        <div className={'controls'}>
          <div className={'group'}>
            <span className={'label'}>Chromosome:</span>
            <select
              value={this.state['chr']} className={'selector button'}
              onChange={(e) => this.selectChr(e.target.value)}>
              {Object.keys(karyotype || {}).map(k => <option key={k} value={k}>Chr {k}</option>)}
            </select>
          </div>
          <div className={'group'}>
            <span className={'label'}>Start:</span>
            {this.renderPosition('start')}
          </div>
          <div className={'group'}>
            <span className={'label'}>End:</span>
            {this.renderPosition('end')}
          </div>
          <div className={'group filters'}>
            <span className={'label'}>Filter:</span>
            <div>{
              Object.keys(this.state['types']).map(name => (
                <label key={`k:${name}`} tabIndex={0} onKeyPress={() => this.changeType(name)} className={'checkbox'}>
                  <input tabIndex={-1} onChange={() => this.changeType(name)} type={'checkbox'} checked={this.state['types'][name]} /> {name} {this.circle(name)}
                </label>
              ))
            }</div>
          </div>
        </div>
        <div className={'karyotype-box'} id={"gmap"} />
        <div className={'signals'}>{this.renderResult()}</div>
      </div>
    )
  }
}

export {Plot, overview};
