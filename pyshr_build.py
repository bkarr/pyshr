from cffi import FFI

ffi = FFI()

ffi.set_source("_pyshr",
    """
        #include <shared_q.h>
        #include <time.h>
        #include <stdlib.h>
    """,
    libraries=["shr", "rt"]
)

ffi.cdef("""

void *malloc(size_t size);
void free(void *ptr);

typedef int... time_t;
struct timespec {
    time_t tv_sec;
    long tv_nsec;
};

typedef enum
{
    SH_OK,                  // success
    SH_RETRY,               // retry previous
    SH_ERR_EMPTY,           // no items on queue
    SH_ERR_LIMIT,           // depth limit reached
    SH_ERR_ARG,             // invalid argument
    SH_ERR_NOMEM,           // not enough memory to satisfy request
    SH_ERR_ACCESS,          // permission error
    SH_ERR_EXIST,           // existence error
    SH_ERR_STATE,           // invalid state
    SH_ERR_PATH,            // problem with path name
    SH_ERR_NOSUPPORT,       // required operation not supported
    SH_ERR_SYS              // system error
} sh_status_e;

typedef struct shr_q shr_q_s;

typedef enum
{
    SQ_EVNT_ALL = 0,        // not an event, used to simplify subscription
    SQ_EVNT_NONE = 0,       // non-event
    SQ_EVNT_INIT,           // first item added to queue
    SQ_EVNT_LIMIT,          // queue limit reached
    SQ_EVNT_TIME,           // max time limit reached
    SQ_EVNT_LEVEL,          // depth level reached
    SQ_EVNT_EMPTY,          // last item on queue removed
    SQ_EVNT_NONEMPTY        // item added to empty queue
} sq_event_e;

typedef enum
{
    SQ_IMMUTABLE = 0,       // queue instance unable to modify queue contents
    SQ_READ_ONLY,           // queue instance able to remove items from queue
    SQ_WRITE_ONLY,          // queue instance able to add items to queue
    SQ_READWRITE            // queue instance can add/remove items
} sq_mode_e;

typedef enum
{
    SH_VECTOR_T = 0,        // vector of multiple types
    SH_STRM_T,              // unspecified byte stream
    SH_INTEGER_T,           // integer data type determined by length
    SH_FLOAT_T,             // floating point type determined by length
    SH_ASCII_T,             // ascii string (char values 0-127)
    SH_UTF8_T,              // utf-8 string
    SH_UTF16_T,             // utf-16 string
    SH_JSON_T,              // json string
    SH_XML_T,               // xml string
    SH_STRUCT_T,            // binary struct
} sh_type_e;

typedef struct sq_vec
{
    uint32_t _zeroes_;      // pad for alignment
    sh_type_e type;         // type of data in vector
    size_t len;             // length of data
    void *base;             // pointer to vector data
} sq_vec_s;

typedef struct  sq_item
{
    sh_status_e status;         // returned status
    sh_type_e type;             // data type
    size_t length;              // length of data being returned
     void *value;               // pointer to data value being returned
    struct timespec *timestamp; // pointer to timestamp of add to queue
    void *buffer;               // pointer to data buffer
    size_t buf_size;            // size of buffer
    int vcount;                 // vector count
    sq_vec_s *vector;           // array of vectors
} sq_item_s;

extern sh_status_e shr_q_create(
    shr_q_s **q,            // address of q struct pointer -- not NULL
    char const * const name,// name of q as a null terminated string -- not NULL
    unsigned int max_depth, // max depth allowed at which add of item is blocked
    sq_mode_e mode          // read/write mode
);


extern sh_status_e shr_q_open(
    shr_q_s **q,            // address of q struct pointer -- not NULL
    char const * const name,// name of q as a null terminated string -- not NULL
    sq_mode_e mode          // read/write mode
);


extern sh_status_e shr_q_close(
    shr_q_s **q         // address of q struct pointer -- not NULL
);


extern sh_status_e shr_q_destroy(
    shr_q_s **q         // address of q struct pointer -- not NULL
);


extern sh_status_e shr_q_monitor(
    shr_q_s *q,         // pointer to queue struct
    int signal          // signal to use for event notification
);


extern sh_status_e shr_q_listen(
    shr_q_s *q,         // pointer to queue struct
    int signal          // signal to use for item arrival notification
);


extern sh_status_e shr_q_call(
    shr_q_s *q,         // pointer to queue struct
    int signal          // signal to use for queue empty notification
);


extern sh_status_e shr_q_add(
    shr_q_s *q,         // pointer to queue struct -- not NULL
    void *value,        // pointer to item -- not NULL
    size_t length       // length of item -- greater than 0
);


extern sh_status_e shr_q_add_wait(
    shr_q_s *q,         // pointer to queue struct -- not NULL
    void *value,        // pointer to item -- not NULL
    size_t length       // length of item -- greater than 0
);


extern sh_status_e shr_q_add_timedwait(
    shr_q_s *q,         // pointer to queue struct -- not NULL
    void *value,        // pointer to item -- not NULL
    size_t length,      // length of item -- greater than 0
    struct timespec *timeout    // timeout value -- not NULL
);


extern sh_status_e shr_q_addv(
    shr_q_s *q,         // pointer to queue struct -- not NULL
    sq_vec_s *vector,   // pointer to vector of items -- not NULL
    int vcnt            // count of vector array -- must be >= 1
);


extern sh_status_e shr_q_addv_wait(
    shr_q_s *q,         // pointer to queue struct -- not NULL
    sq_vec_s *vector,   // pointer to vector of items -- not NULL
    int vcnt            // count of vector array -- must be >= 1
);


extern sh_status_e shr_q_addv_timedwait(
    shr_q_s *q,         // pointer to queue struct -- not NULL
    sq_vec_s *vector,   // pointer to vector of items -- not NULL
    int vcnt,           // count of vector array -- must be >= 1
    struct timespec *timeout    // timeout value -- not NULL
);


extern sq_item_s shr_q_remove(
    shr_q_s *q,         // pointer to queue structure -- not NULL
    void **buffer,      // address of buffer pointer -- not NULL
    size_t *buff_size   // pointer to size of buffer -- not NULL
);


extern sq_item_s shr_q_remove_wait(
    shr_q_s *q,             // pointer to queue struct -- not NULL
    void **buffer,          // address of buffer pointer -- not NULL
    size_t *buff_size       // pointer to size of buffer -- not NULL
);


extern sq_item_s shr_q_remove_timedwait(
    shr_q_s *q,                 // pointer to queue struct -- not NULL
    void **buffer,              // address of buffer pointer -- not NULL
    size_t *buff_size,          // pointer to size of buffer -- not NULL
    struct timespec *timeout    // timeout value -- not NULL
);


extern sq_event_e shr_q_event(
    shr_q_s *q                  // pointer to queue struct -- not NULL
);


extern char *shr_q_explain(
    sh_status_e status          // status code
);


extern bool shr_q_exceeds_idle_time(
    shr_q_s *q,                 // pointer to queue struct -- not NULL
    time_t lim_secs,            // time limit in seconds
    long lim_nsecs              // time limit in nanoseconds
);


extern long shr_q_count(
    shr_q_s *q                  // pointer to queue struct -- not NULL
);


extern size_t shr_q_buffer(
    shr_q_s *q                  // pointer to queue struct -- not NULL
);


extern sh_status_e shr_q_level(
    shr_q_s *q,                 // pointer to queue struct -- not NULL
    int level                   // level at which to generate level event
);


extern sh_status_e shr_q_timelimit(
    shr_q_s *q,                 // pointer to queue struct -- not NULL
    time_t seconds,             // number of seconds till event
    long nanoseconds            // number of nanoseconds till event
);


extern sh_status_e shr_q_clean(
    shr_q_s *q,                 // pointer to queue struct -- not NULL
    struct timespec *timelimit  // timelimit value -- not NULL
);



extern sh_status_e shr_q_last_empty(
    shr_q_s *q,                 // pointer to queue struct -- not NULL
    struct timespec *timestamp  // timestamp pointer -- not NULL
);


extern sh_status_e shr_q_discard(
    shr_q_s *q,                 // pointer to queue struct -- not NULL
    bool flag                   // true will cause items to be discarded
);


extern bool shr_q_will_discard(
    shr_q_s *q                  // pointer to queue struct -- not NULL
);


extern sh_status_e shr_q_limit_lifo(
    shr_q_s *q,                 // pointer to queue struct -- not NULL
    bool flag                   // true will turn on adaptive LIFO behavior
);


extern bool shr_q_will_lifo(
    shr_q_s *q                  // pointer to queue struct -- not NULL
);


extern sh_status_e shr_q_subscribe(
    shr_q_s *q,                 // pointer to queue struct -- not NULL
    sq_event_e event            // event to enable
);


extern sh_status_e shr_q_unsubscribe(
    shr_q_s *q,                 // pointer to queue struct -- not NULL
    sq_event_e event            // event to disable
);


extern bool shr_q_is_subscribed(
    shr_q_s *q,                 // pointer to queue struct -- not NULL
    sq_event_e event            // event to disable
);


extern sh_status_e shr_q_prod(
    shr_q_s *q                  // pointer to queue struct -- not NULL
);


extern long shr_q_call_count(
    shr_q_s *q                  // pointer to queue struct -- not NULL
);


extern sh_status_e shr_q_target_delay(
    shr_q_s *q,                 // pointer to queue struct -- not NULL
    time_t seconds,             // delay number of seconds
    long nanoseconds            // delay number of nanoseconds
);


extern bool shr_q_is_valid(
    char const * const name // name of q as a null terminated string -- not NULL
);
""")

if __name__ == "__main__":
    ffi.compile()
