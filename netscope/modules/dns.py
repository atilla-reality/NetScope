import ipaddress
import os
import random
import socket
import struct
import time


RECORD_TYPES = {
    "A": 1,
    "NS": 2,
    "CNAME": 5,
    "MX": 15,
    "TXT": 16,
    "AAAA": 28,
}

DNS_CLASSES = {
    1: "IN",
}

RCODE_NAMES = {
    0: "NOERROR",
    1: "FORMERR",
    2: "SERVFAIL",
    3: "NXDOMAIN",
    4: "NOTIMP",
    5: "REFUSED",
}


class DNSQueryError(Exception):
    pass


def discover_nameservers():
    servers = []

    try:
        with open("/etc/resolv.conf", "r") as file:
            for line in file:
                fields = line.split()

                if len(fields) >= 2 and fields[0] == "nameserver":
                    try:
                        servers.append(
                            str(ipaddress.ip_address(fields[1]))
                        )
                    except ValueError:
                        continue
    except OSError:
        pass

    return list(dict.fromkeys(servers))


def _encode_name(hostname):
    hostname = hostname.rstrip(".")

    if not hostname:
        raise DNSQueryError("Hostname is empty")

    labels = hostname.split(".")
    encoded = bytearray()

    for label in labels:
        try:
            value = label.encode("idna")
        except UnicodeError:
            raise DNSQueryError("Invalid international hostname")

        if not value or len(value) > 63:
            raise DNSQueryError("Invalid DNS label length")

        encoded.append(len(value))
        encoded.extend(value)

    encoded.append(0)

    if len(encoded) > 255:
        raise DNSQueryError("Hostname is too long")

    return bytes(encoded)


def _decode_name(packet, offset, depth=0):
    if depth > 20:
        raise DNSQueryError("DNS compression depth exceeded")

    labels = []
    position = offset
    next_offset = None
    expanded_length = 1

    while True:
        if position >= len(packet):
            raise DNSQueryError("Invalid DNS name offset")

        length = packet[position]

        if length == 0:
            position += 1

            if next_offset is None:
                next_offset = position

            break

        if length & 0xC0 == 0xC0:
            if position + 1 >= len(packet):
                raise DNSQueryError("Invalid DNS compression pointer")

            pointer = (
                ((length & 0x3F) << 8)
                | packet[position + 1]
            )

            if pointer >= len(packet):
                raise DNSQueryError("DNS pointer out of bounds")

            if next_offset is None:
                next_offset = position + 2

            suffix, unused = _decode_name(
                packet,
                pointer,
                depth + 1,
            )

            if suffix:
                labels.extend(suffix.split("."))

            break

        if length & 0xC0:
            raise DNSQueryError("Invalid DNS label encoding")

        if length > 63:
            raise DNSQueryError("DNS label exceeds 63 bytes")

        position += 1
        end = position + length

        if end > len(packet):
            raise DNSQueryError("DNS label exceeds packet")

        expanded_length += length + 1

        if expanded_length > 255:
            raise DNSQueryError("Expanded DNS name exceeds 255 bytes")

        try:
            labels.append(packet[position:end].decode("ascii"))
        except UnicodeDecodeError:
            raise DNSQueryError("Invalid DNS label encoding")

        position = end

    return ".".join(labels), next_offset


def _build_query(hostname, record_type):
    transaction_id = random.SystemRandom().randint(0, 65535)

    flags = 0x0100
    header = struct.pack(
        "!HHHHHH",
        transaction_id,
        flags,
        1,
        0,
        0,
        0,
    )

    question = (
        _encode_name(hostname)
        + struct.pack("!HH", RECORD_TYPES[record_type], 1)
    )

    return transaction_id, header + question


def _parse_response(packet, expected_id):
    if len(packet) < 12:
        raise DNSQueryError("DNS response is too short")

    (
        transaction_id,
        flags,
        question_count,
        answer_count,
        authority_count,
        additional_count,
    ) = struct.unpack("!HHHHHH", packet[:12])

    if transaction_id != expected_id:
        raise DNSQueryError("DNS transaction ID mismatch")

    if not flags & 0x8000:
        raise DNSQueryError("Packet is not a DNS response")

    if flags & 0x0200:
        raise DNSQueryError("DNS response was truncated")

    if flags & 0x7800:
        raise DNSQueryError("Unexpected DNS opcode")

    rcode = flags & 0x000F

    if rcode:
        name = RCODE_NAMES.get(rcode, "UNKNOWN")
        raise DNSQueryError(
            "DNS server returned {} ({})".format(name, rcode)
        )

    offset = 12

    for unused in range(question_count):
        name, offset = _decode_name(packet, offset)

        if offset + 4 > len(packet):
            raise DNSQueryError("Incomplete DNS question")

        offset += 4

    records = []

    for unused in range(answer_count):
        name, offset = _decode_name(packet, offset)

        if offset + 10 > len(packet):
            raise DNSQueryError("Incomplete DNS resource record")

        (
            record_type,
            record_class,
            ttl,
            length,
        ) = struct.unpack(
            "!HHIH",
            packet[offset:offset + 10],
        )

        offset += 10
        end = offset + length

        if end > len(packet):
            raise DNSQueryError("DNS record exceeds packet")

        data = packet[offset:end]
        value = None

        if record_type == 1:
            if length != 4:
                raise DNSQueryError("Invalid A record length")

            value = socket.inet_ntop(socket.AF_INET, data)

        elif record_type == 28:
            if length != 16:
                raise DNSQueryError("Invalid AAAA record length")

            value = socket.inet_ntop(socket.AF_INET6, data)

        elif record_type in (2, 5):
            value, consumed = _decode_name(packet, offset)

            if consumed != end:
                raise DNSQueryError(
                    "Invalid DNS name record length"
                )

        elif record_type == 15:
            if length < 3:
                raise DNSQueryError("Invalid MX record length")

            preference = struct.unpack("!H", data[:2])[0]
            exchange, consumed = _decode_name(
                packet,
                offset + 2,
            )

            if consumed != end:
                raise DNSQueryError(
                    "Invalid MX record length"
                )

            value = {
                "preference": preference,
                "exchange": exchange,
            }

        elif record_type == 16:
            chunks = []
            cursor = 0

            while cursor < length:
                chunk_length = data[cursor]
                cursor += 1

                if cursor + chunk_length > length:
                    raise DNSQueryError("Invalid TXT record")

                chunks.append(
                    data[cursor:cursor + chunk_length].decode(
                        "utf-8",
                        errors="replace",
                    )
                )

                cursor += chunk_length

            value = chunks

        if value is not None:
            records.append({
                "name": name,
                "type": next(
                    (
                        key for key, number in RECORD_TYPES.items()
                        if number == record_type
                    ),
                    str(record_type),
                ),
                "class": DNS_CLASSES.get(
                    record_class,
                    str(record_class),
                ),
                "ttl": ttl,

                "value": value,

            })

        offset = end

    return records


def _query_server(hostname, record_type, server, timeout):

    transaction_id, packet = _build_query(

        hostname,

        record_type,

    )

    family = (

        socket.AF_INET6

        if ":" in server

        else socket.AF_INET

    )

    with socket.socket(

        family,

        socket.SOCK_DGRAM,

    ) as sock:

        sock.settimeout(timeout)

        destination = (

            (server, 53, 0, 0)

            if family == socket.AF_INET6

            else (server, 53)

        )

        sock.sendto(packet, destination)

        response, address = sock.recvfrom(65535)

    return _parse_response(response, transaction_id)

def _system_lookup(hostname, record_type):

    family = (

        socket.AF_INET

        if record_type == "A"

        else socket.AF_INET6

    )

    results = socket.getaddrinfo(

        hostname,

        None,

        family,

        socket.SOCK_STREAM,

    )

    addresses = sorted({

        item[4][0]

        for item in results

    })

    return [

        {

            "name": hostname,

            "type": record_type,

            "class": "IN",

            "ttl": None,

            "value": address,

        }

        for address in addresses

    ]

def resolve_dns(

    hostname,

    record_types=None,

    server=None,

    timeout=3.0,

):

    started = time.time()

    if record_types is None:

        record_types = ["A", "AAAA"]

    normalized_types = []

    for value in record_types:

        record_type = str(value).upper()

        if record_type not in RECORD_TYPES:

            raise DNSQueryError(

                "Unsupported record type: {}".format(record_type)

            )

        if record_type not in normalized_types:

            normalized_types.append(record_type)

    if not normalized_types:

        raise DNSQueryError("At least one record type is required")

    if timeout <= 0:

        raise DNSQueryError("Timeout must be greater than zero")

    try:

        _encode_name(hostname)

    except DNSQueryError:

        raise

    servers = [server] if server else discover_nameservers()

    if not servers:

        if all(item in ("A", "AAAA") for item in normalized_types):

            results = []

            errors = []

            for record_type in normalized_types:

                try:

                    results.extend(

                        _system_lookup(hostname, record_type)

                    )

                except socket.gaierror as error:

                    errors.append(

                        "{}: {}".format(record_type, error)

                    )

            return {

                "hostname": hostname,

                "resolver": "system resolver",

                "record_types": normalized_types,

                "records": results,

                "status": "ok" if results else "error",

                "errors": errors,

                "elapsed_ms": round(

                    (time.time() - started) * 1000,

                    2,

                ),

            }

        raise DNSQueryError(

            "No DNS nameserver found; specify --server"

        )

    for nameserver in servers:

        try:

            ipaddress.ip_address(nameserver)

        except ValueError:

            raise DNSQueryError(

                "DNS server must be an IP address"

            )

    records = []

    errors = []

    for record_type in normalized_types:

        query_succeeded = False

        last_error = None

        for nameserver in servers:

            try:

                answer = _query_server(

                    hostname,

                    record_type,

                    nameserver,

                    timeout,

                )

                records.extend(answer)

                query_succeeded = True

                break

            except (OSError, DNSQueryError) as error:

                last_error = str(error)

        if not query_succeeded:

            errors.append(

                "{}: {}".format(record_type, last_error)

            )

    return {

        "hostname": hostname,

        "resolver": servers[0],

        "record_types": normalized_types,

        "records": records,

        "status": (

            "ok" if not errors

            else "partial" if records

            else "error"

        ),

        "errors": errors,

        "elapsed_ms": round(

            (time.time() - started) * 1000,

            2,

        ),

    }

