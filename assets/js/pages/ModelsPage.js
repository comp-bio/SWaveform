import React from 'react';
import Loader from "../components/Loader";

const download = (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-download" viewBox="0 0 16 16">
        <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
        <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
    </svg>
);

class ModelsPage extends React.Component {
    constructor(props) {
        super(props);
        this.state = {'data:matrix': {}, 'hmm': false, 'title': false};
        this.loader = new Loader(this);
    }

    componentDidMount() {
        this.loader.get('matrix');
    }

    render() {
        const th = this.state['data:matrix'];
        const matrix = Object.keys(th).map((code, k) => {
            let name = code.split('-');
            return (
                <div className={'model-item'} onClick={() => this.setState({
                    'hmm': th[code].replace('.th.', '.'),
                    'title': code
                })} key={k}>
                    <div className={'hints'}>
                        <span className={'tag'}>{name[0]}</span>
                        <span className={`tag side-${name[1]}`}>{name[1]}</span>
                    </div>
                    <img src={`/models/${th[code]}`} />
                    <div className={'hints hints-bottom'}>
                        <button className={'button'}>Details</button>
                        <a target={'_blank'} href={`/api/model/matrix-${name[0]}-${name[1]}`} className={'button'}>{download} Matrix</a>
                        <a target={'_blank'} href={`/api/model/hmm-${name[0]}-${name[1]}`} className={'button'}>{download} HMM</a>
                    </div>
                </div>
            );
        });

        return (
            <div>
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
                <h2 className="h2">Models</h2>
                <div className={'model-items'}>{matrix}</div>
                {this.state['hmm'] ? (
                    <>
                        <h3 className="h3">{this.state.title}</h3>
                        <div className={'model-hmm'}>
                            <img src={`/models/${this.state.hmm}`}  alt={'hmm'}/>
                        </div>
                    </>
                ) : ''}
            </div>
        );
    }
}

export default ModelsPage;
