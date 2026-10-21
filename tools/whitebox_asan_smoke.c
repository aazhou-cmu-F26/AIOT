/* Harmless AddressSanitizer smoke test: parse one valid CoAP GET PDU. */
#include <coap3/coap.h>

#include <stdio.h>
#include <stdlib.h>

int
main(void) {
  /* CON GET /.well-known/core */
  const uint8_t packet[] = {
      0x40, 0x01, 0x00, 0x01, 0xbb, 0x2e, 0x77, 0x65, 0x6c, 0x6c, 0x2d,
      0x6b, 0x6e, 0x6f, 0x77, 0x6e, 0x04, 0x63, 0x6f, 0x72, 0x65};
  int parse_ok;
  coap_pdu_t *pdu;

  coap_startup();
  pdu = coap_pdu_init(0, 0, 0, 1152);
  if (pdu == NULL) {
    fprintf(stderr, "coap_pdu_init failed\n");
    coap_cleanup();
    return 2;
  }
  parse_ok = coap_pdu_parse(COAP_PROTO_UDP, packet, sizeof(packet), pdu);
  coap_delete_pdu(pdu);
  coap_cleanup();
  if (!parse_ok) {
    fprintf(stderr, "valid smoke PDU failed to parse\n");
    return 1;
  }
  puts("asan_smoke_ok");
  return 0;
}
