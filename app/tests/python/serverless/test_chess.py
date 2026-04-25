from serverless.handlers import matches

def test_bulk_pgn_upload():
    pgn_data = '''[Event "FIDE World Cup 2017"]
[Site "Tbilisi GEO"]
[Date "2017.09.09"]
[Round "4.1"]
[White "Carlsen,M"]
[Black "Bu Xiangzhi"]
[Result "0-1"]
[WhiteElo "2827"]
[BlackElo "2710"]
[EventDate "2017.09.03"]
[ECO "D38"]

1. c4 e6 2. Nc3 d5 3. d4 Nf6 4. Nf3 Bb4 5. Bg5 h6 6. Bh4 dxc4 7. e4 g5
8. Bg3 b5 9. Be2 Bb7 10. O-O a6 11. Ne5 h5 12. h4 g4 13. f3 Nbd7 14. Qc1 
Nxe5 15. Bxe5 Bd6 16. Qg5 Bxe5 17. dxe5 Qd4+ 18. Kh1 Nd7 19. Rad1 Qxe5 
20. Qe3 Qc5 21. Qf4 Qe5 22. Qe3 Qg3 0-1
'''
    res = matches.bulk_upload_pgn({"pgn": pgn_data})
    
    assert res["message"] == "Successfully parsed 1 games"
    
    metadata = res["games_metadata"][0]
    assert metadata["event"] == "FIDE World Cup 2017"
    assert metadata["white"] == "Carlsen,M"
    assert metadata["black"] == "Bu Xiangzhi"
