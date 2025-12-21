from core.advanced import Multiplexer, Demultiplexer, Encoder, Decoder


def test_multiplexer():
    # 2-to-1 MUX (1 select bit)
    mux = Multiplexer(0, 0, select_bits=1)

    # Inputs: [Data0, Data1, Select0]
    # If Select0 is 0, output is Data0
    mux.inputs[0].set_value(True)  # Data0
    mux.inputs[1].set_value(False)  # Data1
    mux.inputs[2].set_value(False)  # Select0
    assert mux.eval() is True

    # If Select0 is 1, output is Data1
    mux.inputs[2].set_value(True)  # Select0
    assert mux.eval() is False

    # 4-to-1 MUX (2 select bits)
    mux4 = Multiplexer(0, 0, select_bits=2)
    # Inputs: [D0, D1, D2, D3, S0, S1]
    mux4.inputs[2].set_value(True)  # D2 is True
    mux4.inputs[4].set_value(False)  # S0=0
    mux4.inputs[5].set_value(True)  # S1=1 (Binary 10 = index 2)
    assert mux4.eval() is True


def test_demultiplexer():
    # 1-to-2 DEMUX (1 select bit)
    demux = Demultiplexer(0, 0, select_bits=1)

    # Inputs: [Data, Select0]
    demux.inputs[0].set_value(True)  # Data=1
    demux.inputs[1].set_value(False)  # Select0=0
    demux.update()
    assert demux.outputs[0].get_value() is True
    assert demux.outputs[1].get_value() is False

    demux.inputs[1].set_value(True)  # Select0=1
    demux.update()
    assert demux.outputs[0].get_value() is False
    assert demux.outputs[1].get_value() is True


def test_encoder():
    # 4-to-2 Priority Encoder
    encoder = Encoder(0, 0, num_inputs=4)

    # Highest active input index should be encoded to binary
    encoder.inputs[1].set_value(True)
    encoder.update()
    # Output 1 is True (Binary 01)
    assert encoder.outputs[0].get_value() is True
    assert encoder.outputs[1].get_value() is False

    # Priority: if input 3 is also true, output should be 3 (Binary 11)
    encoder.inputs[3].set_value(True)
    encoder.update()
    assert encoder.outputs[0].get_value() is True
    assert encoder.outputs[1].get_value() is True


def test_decoder():
    # 2-to-4 Decoder
    decoder = Decoder(0, 0, num_inputs=2)

    # Input 0: Binary 00 -> Output 0 active
    decoder.inputs[0].set_value(False)
    decoder.inputs[1].set_value(False)
    decoder.update()
    assert decoder.outputs[0].get_value() is True
    assert all(not decoder.outputs[i].get_value() for i in range(1, 4))

    # Input 3: Binary 11 -> Output 3 active
    decoder.inputs[0].set_value(True)
    decoder.inputs[1].set_value(True)
    decoder.update()
    assert decoder.outputs[3].get_value() is True
    assert all(not decoder.outputs[i].get_value() for i in range(0, 3))
