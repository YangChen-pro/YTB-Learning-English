from youtube_vocab.transcripts.vtt import parse_vtt_captions


def test_parse_vtt_captions_with_cue_ids_and_settings() -> None:
    text = """\ufeffWEBVTT\r
\r
first-cue\r
00:00:05.332 --> 00:00:12.956 align:start position:0%\r
I've heard that... the rules\r
that govern this world are curses\r
\r
01:02.500 --> 01:04.000\r
Second cue\r
"""

    captions = parse_vtt_captions(text)

    assert len(captions) == 2
    assert captions[0].start == 5.332
    assert captions[0].duration == 7.624
    assert captions[0].text == "I've heard that... the rules that govern this world are curses"
    assert captions[1].start == 62.5
    assert captions[1].duration == 1.5

