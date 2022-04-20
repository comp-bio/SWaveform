import React from 'react'
import { examples, schema, download } from '../components/helpers.js'

const overview = require('../../../build/overview.json');

class DescriptionPage extends React.Component {
  constructor(props) {
    super(props);
    this.examples = examples();
    this.schema = schema();
    this.state = {};
    
    console.log('schema', this.schema.compact);
  }
  
  iter(name, ds) {
    return  '';
    return (
      <table className={'mini-table'}>
        <thead><tr><th>Type</th><th>Count</th></tr></thead>
        <tbody>{
          Object.keys(overview['ds'][ds][name]).filter(v => v != '').map((v, k) => {
            return <tr key={k}><td key={'v'+k}>{v}</td><td key={'k'+k}>{overview['ds'][ds][name][v]}</td></tr>
          })
        }</tbody>
      </table>
    )
  }
  
  componentDidMount() {
    this.setState({
    });
  }
  
  render() {
    return (
      <div>
        <div className={'part'}>
          <p className="lead">
            The coverage signal database contains data on genome coverage in the vicinity of breakpoints of structural variants (table <code>signal</code>).
            All coverage values are stored without normalization and without compression.
            For each signal, the database indicates which of the breakpoints of the structural variant was used: left (L) or right (R).
            For each signal, the database stores information about the sample from which it was received (table <code>target</code>).
            In the visualization, the breakpoint is located exactly in the center (highlighted with a vertical red line).
            The horizontal blue line is the average coverage for the sample from which the signal was derived.
            Data source: Human Genome Diversity Project (HGDP).
          </p>
        </div>

        <h2 className="h2">
          <span>Schema</span>
          <div className={'group'}>
            <button className={'button'}
                    onClick={() => { download('schema.json', this.schema.documents) }}>JSON</button>
            <button className={'button'}
                    onClick={() => { download('schema.sql', this.schema.sqlite, 'application/octet-stream') }}>SQLite</button>
          </div>
        </h2>

        <div className={'part tables'}>
          {this.schema.compact.map((table, k) => (
            <div key={k} className="col">
              <h4 className="h4">Table: <code>{table.name}</code></h4>
              <table>
                <thead><tr><th>Column</th><th>Description</th></tr></thead>
                <tbody>
                {table.columns.map((row,r) => (
                  <tr key={r}>
                    <td>{row.name} <code>{row.type.datatype}</code></td>
                    <td>{row.options.comment}</td>
                  </tr>
                ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>

        <h2 className="h2">
          <span>Code examples</span>
          <div className={'group tabs'}>
            <button className={'button active'}>Python</button>
            <button className={'button'}>PHP</button>
            <button className={'button'}>R</button>
          </div>
          
        </h2>
        <div className={'part'}>
          <h4 className="h4">Python</h4>
          <div className={'code'} dangerouslySetInnerHTML={{ __html: this.examples['hl.py'] }} />
          <h4 className="h4">PHP</h4>
          <div className={'code'} dangerouslySetInnerHTML={{ __html: this.examples['hl.php'] }} />
          <h4 className="h4">R</h4>
          <div className={'code'} dangerouslySetInnerHTML={{ __html: this.examples['hl.r'] }} />
        </div>
        
        <h2 className="h2">Statistics</h2>
        <div className={'part stat'}>
          <h4 className={'h4'}>Total signals in database:</h4>
          <div className={'items'}><code>{overview.total.toLocaleString()}</code></div>
          <div className={'dataset-groups'}>
            {Object.keys(overview['ds']).map(ds => {
              //let p = this.iter('populations', ds);
              return (
                <div className={'dataset-group'} key={ds}>
                  <h4 className={'h4'}>Dataset: <strong>{ds}</strong></h4>
                  {this.iter('types', ds)}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }
}

export default DescriptionPage;
