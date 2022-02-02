import React from "react";
import KaryotypeBar from "./KaryotypeBar";
import Signal from "./Signal";
import LoadSignal from "./LoadSignal";

const d3 = require('d3')
const overview = require('../../../build/overview.json')
const karyotypes = {
  'GRCh37': require('../../../data/GRCh37.json'),
  'GRCh38': require('../../../data/GRCh38.json')
}

const types = Object.values(overview['ds']).map(v => Object.keys(v['types'])).flat();
const type_color = d3.scaleOrdinal().domain(types).range(d3.schemeTableau10);

let timer = null;

class Plot extends React.Component {
  constructor(props) {
    super(props);

    this.karyotypes = karyotypes;
    this.overview = overview;

    this.state = {
      'dataset': '', 'karyotype': {},
      'chr': '', 'start': 0, 'end': 1, 'offset': 0,
      'data:signal': [], 'types': {},
      'more': true,
      'windowWidth': window.innerWidth
    };

    types.map(k => { this.state['types'][k] = true; });

    this.loader = new LoadSignal(this);
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
      if (type === 'end') this.loader.get();
    });
  }

  componentDidMount() {
    this.selectDataset(Object.keys(overview['ds'])[0]);
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

  selectDataset(name) {
    let types = {};
    Object.keys(overview['ds'][name]['types']).map(k => { types[k] = true; })

    this.setState({
      'types': types,
      'dataset': name,
      'karyotype': karyotypes[overview['ds'][name]['genome']] || [],
    }, () => {
      this.gmap = KaryotypeBar('#gmap', this);
      if (!this.state['chr']) this.selectChr('1');
    });
  }

  selectChr(val) {
    let c = this.state['karyotype'][val];
    const offset = c[c.length - 1][1] / 40;
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

  changeKey(name, key) {
    this.setState(prevState => {
      prevState[key][name] = !prevState[key][name];
      return {[key]: prevState[key]};
    }, () => {
      this.gmap = KaryotypeBar('#gmap', this);
      this.loader.get();
    });
  }

  renderResult() {
    let items = [];
    if (this.state['data:signal'].length) {
      items = this.state['data:signal'].map((e, k) => {
        return (
          <div className={'signal-wrapper'} key={k}>
            <div className={'hints'}>
              <span>
                <span className={'circle'} style={{background: type_color(e.type)}} />
                <span className={'tag'}>{e.type}</span>
                <span className={`tag side-${e.side}`}>{e.side}</span>
              </span>
              <span>
                <span className={'tag mini'}>{e.name}</span>
              </span>
            </div>
            <Signal obj={e} parent={this} />
          </div>
        );
      });

      if (this.state['more'] && items.length >= 24) {
        items.push(
            <div className={'load-more'} key={'loader'}>
              <a onClick={() => {
                if (this.state['loading:signal']) return null;
                this.loader.get(true);
              }} className={'button'}>{this.state['loading:signal'] ? '...' : 'Load more'}</a>
            </div>
        );
      }
    }

    if (this.state['loading:signal']) {
      items.push(<div key={'loading'} className={'placeholder'}>Loading...</div>)
    }

    if (items.length > 0) {
      return <>{items}</>;
    }

    return (<div className={'placeholder'}>No coverage signals loaded for this region</div>)
  }

  checkbox(name, key, color) {
    return (
        <label key={`k:${name}`} tabIndex={0} onKeyPress={() => this.changeKey(name, key)} className={'checkbox'}>
          <input tabIndex={-1} onChange={() => this.changeKey(name, key)} type={'checkbox'} checked={this.state[key][name]} /> {name}
          <span className={'circle'} style={{background: color(name)}} />
        </label>
    );
  }

  render() {
    return (
      <div>
        <div className={'controls'}>
          <div className={'group filters'}>
            <span className={'label'}>Dataset:</span>
            <select
                value={this.state['dataset']} className={'selector button'}
                onChange={(e) => this.selectDataset(e.target.value)}>
              {Object.keys(overview['ds']).map(k => <option key={k} value={k}>{k} ({overview['ds'][k]['genome']})</option>)}
            </select>
          </div>
          <div className={'group filters'}>
            <span className={'label'}>Filter by type:</span>
            <div>{Object.keys(this.state['types']).map(name => this.checkbox(name, 'types', type_color))}</div>
          </div>
        </div>
        <div className={'controls'}>

          <div className={'group'}>
            <span className={'label'}>Chromosome:</span>
            <select
              value={this.state['chr']} className={'selector button'}
              onChange={(e) => this.selectChr(e.target.value)}>
              {Object.keys(this.state['karyotype'] || {}).map(k => <option key={k} value={k}>Chr {k}</option>)}
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
        </div>
        <div className={'karyotype-box'} id={"gmap"} />
        <div className={'signals'}>{this.renderResult()}</div>
      </div>
    )
  }
}

export {Plot, overview};
