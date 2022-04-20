import React from 'react';
import axios from 'axios';

const download = (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-download" viewBox="0 0 16 16">
        <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
        <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
    </svg>
);

class ModelsPage extends React.Component {
    constructor(props) {
        super(props);
        this.state = {'th': {}, 'hmm': false, 'title': false};
    }

    componentDidMount() {
        axios({
            url: `/api/matrix`,
            method: 'get'
        }).then((res) => {
            this.setState({'th': res.data});
        });
    }

    render() {
        return (
            <>
                <div className={'part'}>
                    <p className="lead">
                        All signals are compressed to a 64x32 matrix. All matrices for all signals are summed and normalized.
                        The intensity of the blue squares shows the number of signal values for a given point (Matrix.json).
                    </p>
                    <p className="lead">
                        Markov models (HMM.json) were built for all signals of each type as follows:
                        For each value of the coverage signal at position <code>i</code>, the probabilities of transition to all possible values of position <code>i + 1</code> are calculated.
                        The probabilities are highlighted on the chart with lines. Line intensity is close to 1.
                    </p>
                </div>
                {Object.keys(this.state['th']).map((ds, kds) => {
                    return (
                        <div key={kds}>
                            <h2 className="h2">Models ({ds})</h2>
                            <div className={'model-items'}>{
                                Object.keys(this.state['th'][ds]).map((code, k) => {
                                    let name = code.split('-');
                                    return (
                                        <div className={'model-item'} onClick={() => this.setState({
                                            'hmm': this.state['th'][ds][code].replace('.th.', '.'),
                                            'title': code
                                        })} key={k}>
                                            <div className={'hints'}>
                                                <span className={'tag'}>{name[1]}</span>
                                                <span className={`tag side-${name[2]}`}>{name[2]}</span>
                                            </div>
                                            <img src={`/models/${this.state['th'][ds][code]}`} />
                                            <div className={'hints hints-bottom'}>
                                                <button className={'button'}>Details</button>
                                                <a target={'_blank'} href={`/api/model/mat-${name[0]}-${name[1]}-${name[2]}`} className={'button'}>{download} Matrix</a>
                                                <a target={'_blank'} href={`/api/model/hmm-${name[0]}-${name[1]}-${name[2]}`} className={'button'}>{download} HMM</a>
                                            </div>
                                        </div>
                                    );
                                })
                            }</div>
                        </div>
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
