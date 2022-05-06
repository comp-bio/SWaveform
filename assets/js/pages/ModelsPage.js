import React from 'react';
import axios from 'axios';

const icon = (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-download" viewBox="0 0 16 16">
        <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
        <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
    </svg>
);

class ModelsPage extends React.Component {
    constructor(props) {
        super(props);
        this.state = {'models': [], 'meta': [], 'hmm': false, 'title': false};
    }

    componentDidMount() {
        axios({url: `/api/overview`, method: 'get'}).then((res) => {
            this.setState(res.data);
            res.data.meta.map(src => {
                axios({url: `/downloads/${src}`, method: 'get'}).then((res) => {
                    this.setState({[`src:${src}`]: res.data})
                });
            });
        });
    }
    
    gridPlot(C) {
        if (!C) return '';
        return (
          <article className={'cluster'} key={C.name + C.part}>
              <h5>{C.name} <code>{C.part}</code></h5>
              <div className={'plot-list'}>
                  <img className={'img'} src={`data:image/png;base64,${C.cluster}`}  alt={'Cluster'} />
                  {C.motif.map(m => (
                    <div key={m.file} className={'img'}>
                        <img src={`data:image/png;base64,${m.plot}`} alt={'Motif'} />
                        <a target={'_blank'} href={`/downloads/${m.file}`} className={'button'}>{icon} Download</a>
                    </div>
                  ))}
              </div>
          </article>
        );
    }

    render() {
        return (
            <>
                <div className={'part'}>
                    <p className="lead">
                      The graphs show all signals of each type, overlapping each other.
                      SAX-transformation is used with a width of 128 and the size of the alphabet 32
                    </p>
                </div>

                <h2 className="h2">SV overview</h2>
                <div className={'model-items'}>
                    {this.state.models.map(src => <div className={'model-item'} key={src}><img src={`/models/${src}`} /></div>)}
                </div>
    
                <h2 className="h2">Found motifs</h2>
                <div className={'part'}>
                  <p className="lead">
                    1 column:<br/>
                    For all signals from the cluster, the average value (blue line) and the standard deviation (gray strip) are shown.
                    All runs (all clusters) are superimposed on each other. Standard normalization is applied.
                  </p>
                  <p className="lead">
                    2-5 columns:<br/>
                    4 of the most significant motives. Gray lines show a signal from which the motive is extracted, the motive itself is highlighted by orange. SAX-transformation is applied).
                  </p>
                </div>
                {this.state.meta.map(src => {
                    const obj = this.state[`src:${src}`] || null;
                    if (!obj) return <div key={src} className={'meta-item'}>{src}</div>;
                    return (
                      <div className={'cluster-group'}>{obj.map(this.gridPlot)}</div>
                    );
                })}
                
                <div className={'modal ' + (this.state['hmm'] ? 'visible' : '')}>
                    <div className={'container'}>
                        <div className={'modal-head'}>
                            <span className="modal-title">{this.state.title}</span>
                            <a className={'modal-close'} onClick={() => this.setState({'hmm': false})}><span>×</span></a>
                        </div>
                        <div className={'model-hmm'}>
                            <img src={`/models/${this.state.hmm}`}  alt={'hmm'}/>
                        </div>
                    </div>
                    <div onClick={() => this.setState({'hmm': false})} className={'bg'} />
                </div>
            </>
        );
    }
}

export default ModelsPage;
