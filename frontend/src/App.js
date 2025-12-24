import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [telegrams, setTelegrams] = useState([]);
  const [selectedTelegram, setSelectedTelegram] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 検索用State
  const [searchParams, setSearchParams] = useState({ number: '', version: '' });
  // オーダ番号入力欄への参照を追加
  const numberInputRef = useRef(null);
  const versionInputRef = useRef(null);

  // 初回ロード時に一覧を取得
  useEffect(() => {
    fetchTelegrams();
  }, []);

  // 電文一覧取得
  const fetchTelegrams = async () => {
    try {
      const res = await axios.get('/api/telegrams');
      setTelegrams(res.data);
    } catch (err) {
      console.error("Fetch error:", err);
      setError("データの取得に失敗しました。");
    }
  };

  // 検索実行
  const executeSearch = async (number, version) => {
    setLoading(true);
    setError(null);
    try {
      // API呼び出し
      const res = await axios.get('/api/telegrams/search', {
        params: {
          order_number: number,
          version: version
        }
      });
      const searchResults = res.data;
      setTelegrams(searchResults);

      // 検索結果判定
      if (searchResults.length > 0) {
        // 該当あり: 先頭の電文を自動選択して詳細を表示
        handleSelectTelegram(searchResults[0].id);
      } else {
        // ★該当なし: 詳細画面をクリア（選択解除）
        setSelectedTelegram(null);
      }

    } catch (err) {
      console.error("Search error:", err);
      setError("検索に失敗しました。");
    } finally {
      setLoading(false);
    }
  };

  // オーダ番号入力ハンドラ
  const handleSearchNumberChange = (e) => {
    const val = e.target.value;
    // 数値のみ入力可
    if (!/^\d*$/.test(val)) return;

    if (val.length <= 8) {
      setSearchParams(prev => ({ ...prev, number: val }));
      
      // 8桁入力されたら版数へフォーカス移動
      if (val.length === 8) {
        versionInputRef.current.focus();
      }
    }
  };

  // 版数入力ハンドラ
  const handleSearchVersionChange = (e) => {
    const val = e.target.value;
    if (!/^\d*$/.test(val)) return;

    if (val.length <= 2) {
      setSearchParams(prev => ({ ...prev, version: val }));

      // 2桁入力されたら自動検索実行
      if (val.length === 2) {
        executeSearch(searchParams.number, val);
      }
    }
  };

  // ファイル選択ハンドラ
  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  // アップロード実行ハンドラ
  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    setError(null);

    try {
      await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      await fetchTelegrams();
      setFile(null);
      alert("アップロードと解析が完了しました。");
    } catch (err) {
      console.error("Upload error:", err);
      setError("アップロードまたは解析に失敗しました。");
    } finally {
      setLoading(false);
    }
  };

  // 詳細データの取得
  const handleSelectTelegram = async (id) => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`/api/telegrams/${id}`);
      setSelectedTelegram(res.data);
    } catch (err) {
      console.error("Detail fetch error:", err);
      setError("詳細データの取得に失敗しました。");
    } finally {
      setLoading(false);
    }
  };

  // 日付フォーマット用ヘルパー
  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleString('ja-JP');
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>注射オーダ電文照会システム</h1>
      </header>

      <main className="App-container">
        {/* エラー表示 */}
        {error && <div className="error-message">{error}</div>}

        {/* 検索セクション */}
        <section className="search-section">
          <h2>電文検索</h2>
          <div className="search-form">
            <div className="input-group">
              <label>オーダ番号</label>
              <input
                type="text"
                placeholder="8桁"
                value={searchParams.number}
                onChange={handleSearchNumberChange}
                disabled={loading}
                ref={numberInputRef}
              />
            </div>
            <div className="input-group">
              <label>版数</label>
              <input
                type="text"
                placeholder="2桁"
                value={searchParams.version}
                onChange={handleSearchVersionChange}
                disabled={loading}
                ref={versionInputRef}
              />
            </div>
            <button 
              type="button" 
              onClick={() => {
                setSearchParams({number: '', version: ''});
                fetchTelegrams();
                setSelectedTelegram(null); // クリア時も詳細をリセット
                // クリア時にオーダ番号へフォーカス
                if (numberInputRef.current) {
                  numberInputRef.current.focus();
                }
              }}
              className="secondary-button"
            >
              クリア
            </button>
          </div>
        </section>

        {/* 1. ファイルアップロードセクション */}
        <section className="upload-section">
          <h2>新規電文取込</h2>
          <form onSubmit={handleUpload} className="upload-form">
            <input 
              type="file" 
              onChange={handleFileChange} 
              disabled={loading}
              accept=".txt,.dat,.bin" 
            />
            <button type="submit" disabled={!file || loading}>
              {loading ? '処理中...' : '解析・保存'}
            </button>
          </form>
        </section>

        <div className="content-area">
          {/* 2. 左側: 電文リスト */}
          <section className="list-section">
            <h2>受信履歴 / 検索結果</h2>
            {telegrams.length === 0 ? (
              <p style={{padding: '20px', color: '#666'}}>データがありません</p>
            ) : (
              <ul className="telegram-list">
                {telegrams.map((t) => (
                  <li 
                    key={t.id} 
                    onClick={() => handleSelectTelegram(t.id)}
                    className={selectedTelegram && selectedTelegram.id === t.id ? 'active' : ''}
                  >
                    <div className="list-item-header">
                      <span className="patient-name">{t.patient_name || '名称不明'}</span>
                      <span className="patient-id">ID: {t.patient_id}</span>
                    </div>
                    <div className="list-item-sub">
                      No: {t.order_number} (v{t.version})<br/>
                      オーダ日: {t.order_date || '-'}<br/>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* 3. 右側: 詳細表示 */}
          <section className="detail-section">
            <h2>電文詳細</h2>
            {!selectedTelegram ? (
              <div className="placeholder">左のリストから選択してください</div>
            ) : (
              <div className="detail-content">
                
                {/* 処方項目一覧 */}
                <div className="info-group">
                  <h3>処方項目一覧</h3>
                  <table className="item-table">
                    <thead>
                      <tr>
                        <th>項目名</th>
                        <th>数量</th>
                        <th>単位</th>
                        <th>コード</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedTelegram.raw_data?.content?.item_group?.item_info
                        ?.filter(item => item.attribute === 'ID1').map((item, index) => (
                          <tr key={index}>
                            <td>{item.name}</td>
                            <td>{item.quantity}</td>
                            <td>{item.unit_name}</td>
                            <td>{item.code}</td>
                          </tr>
                        )) || (
                          <tr><td colSpan="4">項目なし</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>

                {/* 患者情報 */}
                <div className="info-group">
                  <h3>患者情報</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <label>患者ID</label>
                      <span>{selectedTelegram.patient_id}</span>
                    </div>
                    <div className="info-item">
                      <label>患者氏名</label>
                      <span>{selectedTelegram.patient_name}</span>
                    </div>
                    <div className="info-item">
                      <label>生年月日</label>
                      <span>{selectedTelegram.raw_data?.content?.patient_info?.birthdate || '-'}</span>
                    </div>
                    <div className="info-item">
                      <label>住所</label>
                      <span>{selectedTelegram.raw_data?.content?.patient_info?.address || '-'}</span>
                    </div>
                  </div>
                </div>

                {/* オーダ情報 */}
                <div className="info-group">
                  <h3>オーダ情報</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <label>オーダ番号</label>
                      <span>{selectedTelegram.raw_data?.content?.order_info?.number || '-'}</span>
                    </div>
                    <div className="info-item">
                      <label>版数</label>
                      <span>{selectedTelegram.raw_data?.content?.order_info?.version || '-'}</span>
                    </div>
                    <div className="info-item">
                      <label>依頼医ID</label>
                      <span>{selectedTelegram.raw_data?.content?.order_info?.doctor_info?.d_id || '-'}</span>
                    </div>
                    <div className="info-item">
                      <label>依頼医氏名</label>
                      <span>{selectedTelegram.raw_data?.content?.order_info?.doctor_info?.kanji_name || '-'}</span>
                    </div>
                    <div className="info-item">
                      <label>診療科</label>
                      <span>{selectedTelegram.raw_data?.content?.order_info?.hakkou_dept_code || '-'}</span>
                    </div>
                  </div>
                </div>

                <div className="info-group">
                  <h3>取込情報</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <label>取込日時</label>
                      <span>{formatDate(selectedTelegram.created_at)}</span>
                    </div>
                    <div className="info-item">
                      <label>最終更新日時</label>
                      <span>{formatDate(selectedTelegram.updated_at)}</span>
                    </div>
                    <div className="info-item">
                      <label>JSON</label>
                      <pre>{JSON.stringify(selectedTelegram.raw_data, null, 2)}</pre>
                    </div> 
                  </div>
                </div>
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

export default App;